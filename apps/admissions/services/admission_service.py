"""
Admission service — encapsulates the full workflow state transitions
and the side effects (student creation, admission challan, notifications).
"""
from __future__ import annotations
from typing import Optional
from django.db import transaction
from django.utils import timezone

from apps.students.models import Student, RegistrationNumberService, StudentEnrollment
from apps.students.models import Student as StudentModel

from ..models import Admission, ApplicationNumberService


class AdmissionWorkflowError(Exception):
    pass


class AdmissionService:
    """All non-trivial admission transitions live here."""

    # Allowed forward transitions
    TRANSITIONS = {
        Admission.Status.DRAFT: {Admission.Status.SUBMITTED, Admission.Status.CANCELLED},
        Admission.Status.SUBMITTED: {Admission.Status.VERIFIED, Admission.Status.REJECTED, Admission.Status.CANCELLED},
        Admission.Status.VERIFIED: {Admission.Status.APPROVED, Admission.Status.REJECTED},
        Admission.Status.APPROVED: {Admission.Status.REGISTERED},
        Admission.Status.REGISTERED: {Admission.Status.COMPLETED},
        Admission.Status.COMPLETED: set(),
        Admission.Status.REJECTED: set(),
        Admission.Status.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, current, target):
        return target in cls.TRANSITIONS.get(current, set())

    @classmethod
    @transaction.atomic
    def submit(cls, admission: Admission, user) -> Admission:
        if not cls.can_transition(admission.status, Admission.Status.SUBMITTED):
            raise AdmissionWorkflowError(f"Cannot submit from status {admission.status}")
        if not admission.application_no:
            admission.application_no = ApplicationNumberService.generate()
        admission.status = Admission.Status.SUBMITTED
        admission.save()
        return admission

    @classmethod
    @transaction.atomic
    def verify(cls, admission: Admission, user) -> Admission:
        if not cls.can_transition(admission.status, Admission.Status.VERIFIED):
            raise AdmissionWorkflowError("Application must be in SUBMITTED state to verify.")
        admission.status = Admission.Status.VERIFIED
        admission.reviewed_by = user
        admission.save()
        return admission

    @classmethod
    @transaction.atomic
    def approve(cls, admission: Admission, user) -> Admission:
        if not cls.can_transition(admission.status, Admission.Status.APPROVED):
            raise AdmissionWorkflowError("Application must be in VERIFIED state to approve.")
        admission.status = Admission.Status.APPROVED
        admission.reviewed_by = user
        admission.save()
        return admission

    @classmethod
    @transaction.atomic
    def reject(cls, admission: Admission, user) -> Admission:
        if not cls.can_transition(admission.status, Admission.Status.REJECTED):
            raise AdmissionWorkflowError("Application cannot be rejected from current state.")
        admission.status = Admission.Status.REJECTED
        admission.reviewed_by = user
        admission.save()
        return admission

    @classmethod
    @transaction.atomic
    def register_student(cls, admission: Admission, user) -> tuple[StudentModel, Admission]:
        """Creates the Student record linked to this admission.

        Race-safety: we lock the Admission row first (SELECT ... FOR UPDATE),
        then re-check `admission.student`. This guarantees that two concurrent
        calls to register_student on the same admission cannot both create a
        Student record — only the first wins, the second sees the FK populated
        and returns early.
        """
        # Lock the admission row — serializes parallel register_student calls.
        admission = Admission.objects.select_for_update().get(pk=admission.pk)

        # Re-check status and student AFTER acquiring the lock — another
        # concurrent call may have just transitioned the admission.
        if not cls.can_transition(admission.status, Admission.Status.REGISTERED):
            # Idempotent: if the admission already has a student linked, just
            # return that student (covers a parallel-call race).
            if admission.student:
                return admission.student, admission
            raise AdmissionWorkflowError("Admission must be APPROVED before registering a student.")

        if admission.student:
            return admission.student, admission

        from apps.parents.models import Parent
        # Handle blank CNIC — use a unique fallback so we don't attach all
        # blank-CNIC parents to the same shared Parent record.
        parent_cnic = admission.parent_cnic or f"TEMP-{admission.pk}"
        parent, _ = Parent.objects.get_or_create(
            cnic=parent_cnic,
            defaults={
                "full_name": admission.parent_name,
                "relation": Parent.Relation.FATHER,
                "phone": admission.parent_phone,
                "occupation": admission.parent_occupation,
                "address": admission.address,
            },
        )

        # Create the student. We can't use get_or_create here because each new
        # student gets a freshly-generated registration_no, which is by
        # definition unique — so get_or_create would always CREATE. The race
        # protection comes from the admission-row lock above: only the call that
        # wins the lock reaches this line; the other call sees admission.student
        # set and returns early.
        student = Student.objects.create(
            registration_no=RegistrationNumberService.generate(),
            full_name=admission.full_name,
            father_name=admission.father_name,
            mother_name=admission.mother_name,
            date_of_birth=admission.date_of_birth,
            gender=admission.gender,
            cnic_or_bform=admission.cnic_bform,
            address=admission.address,
            previous_school=admission.previous_school,
            previous_class=admission.previous_class,
            contact_phone=admission.contact_phone,
            email=admission.email,
            parent=parent,
            current_class=admission.applying_class,
            current_section=admission.applying_section,
            admission_date=admission.admission_date,
            status=Student.Status.ACTIVE,
        )

        StudentEnrollment.objects.create(
            student=student,
            academic_year=admission.academic_year,
            school_class=admission.applying_class,
            section=admission.applying_section,
            is_current=True,
        )

        admission.student = student
        admission.status = Admission.Status.REGISTERED
        admission.save()
        return student, admission

    @classmethod
    @transaction.atomic
    def generate_admission_challan(cls, admission: Admission, user) -> "FeeChallan":
        """Generate an admission fee challan for this admission.

        The FeeChallan model requires a non-null Student FK, so we make sure
        the student record exists first (calling register_student is idempotent —
        if the student is already linked, it just returns the existing one).
        """
        # Ensure the student is registered before creating a challan linked to it.
        if not admission.student:
            cls.register_student(admission, user)
            admission.refresh_from_db()
        if admission.admission_challan:
            return admission.admission_challan
        from apps.fees.services.fee_service import FeeService
        from apps.fees.models import FeeType
        admission_fee_type, _ = FeeType.objects.get_or_create(
            name="Admission Fee",
            defaults={
                "code": "ADM",
                "fee_type": "admission",
                "default_amount": 5000,
                "is_active": True,
            },
        )
        challan = FeeService.generate_admission_challan(admission, admission_fee_type, user)
        admission.admission_challan = challan
        admission.save()
        return challan

    @classmethod
    @transaction.atomic
    def complete_after_payment(cls, admission: Admission, user) -> Admission:
        """Called when the admission challan is paid."""
        # Lock the admission to serialize complete_after_payment attempts.
        admission = Admission.objects.select_for_update().get(pk=admission.pk)
        if not admission.admission_challan:
            raise AdmissionWorkflowError("Admission challan not generated yet.")
        # Use the FeeChallan.Status enum, not a magic string, for type safety.
        from apps.fees.models import FeeChallan
        paid_status = FeeChallan.Status.PAID
        if admission.admission_challan.status != paid_status:
            raise AdmissionWorkflowError("Admission challan is not yet paid.")
        # Idempotent — if the admission is already COMPLETED, just return it.
        if admission.status == Admission.Status.COMPLETED:
            return admission
        admission.status = Admission.Status.COMPLETED
        admission.save()
        return admission
