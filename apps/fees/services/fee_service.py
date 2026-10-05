"""
FeeService — encapsulates all fee business logic:
- monthly challan generation
- admission challan generation
- late fee calculation
- payment recording (transaction-safe)
- challan status updates
"""
from __future__ import annotations
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.students.models import Student
from apps.common.models import AcademicYear
from ..models import (
    FeeChallan, FeeChallanItem, FeePayment, FeeStructure,
    ChallanNumberService, ReceiptNumberService,
)


class FeeService:

    # -------------------------------------------------------------------
    # Late fee — flat amount after SCHOOL_LATE_FEE_DAYS days past due_date
    # -------------------------------------------------------------------
    @staticmethod
    def calculate_late_fee(challan: FeeChallan) -> Decimal:
        if not challan.due_date:
            return Decimal("0")
        if challan.status == FeeChallan.Status.PAID:
            return Decimal("0")
        today = timezone.now().date()
        if today <= challan.due_date:
            return Decimal("0")
        late_days = (today - challan.due_date).days
        # Apply late fee once after the grace period
        if late_days > settings.SCHOOL_LATE_FEE_DAYS:
            return Decimal(settings.SCHOOL_LATE_FEE_AMOUNT)
        return Decimal("0")

    # -------------------------------------------------------------------
    # Generate monthly challan for a single student
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def generate_monthly_challan(
        cls,
        student: Student,
        month_label: str,
        academic_year: Optional[AcademicYear] = None,
        user=None,
    ) -> FeeChallan:
        academic_year = academic_year or AcademicYear.objects.get_active()
        if not academic_year:
            raise ValueError("No active academic year.")

        if not student.current_class:
            raise ValueError(f"Student {student.full_name} has no current class assigned.")

        # Idempotency: don't duplicate monthly challan for same month
        existing = FeeChallan.objects.filter(
            student=student, academic_year=academic_year,
            month=month_label, is_admission_challan=False,
        ).exclude(status=FeeChallan.Status.CANCELLED).first()
        if existing:
            return existing

        challan = FeeChallan.objects.create(
            challan_no=ChallanNumberService.generate(),
            student=student,
            academic_year=academic_year,
            month=month_label,
            due_date=cls._due_date_for_month(month_label),
            status=FeeChallan.Status.UNPAID,
            created_by=user,
        )

        structures = FeeStructure.objects.filter(
            academic_year=academic_year,
            school_class=student.current_class,
            fee_type__is_active=True,
            applies_monthly=True,
            is_active=True,
        )
        if not structures.exists():
            # fall back to a single default Tuition type with the structure's amount = 0
            from ..models import FeeType
            tuition, _ = FeeType.objects.get_or_create(
                code="TUI",
                defaults={"name": "Tuition Fee", "fee_type": "tuition", "default_amount": 0}
            )
            FeeChallanItem.objects.create(
                challan=challan, fee_type=tuition, amount=tuition.default_amount or 0,
            )
        else:
            for s in structures:
                FeeChallanItem.objects.create(
                    challan=challan,
                    fee_type=s.fee_type,
                    amount=s.amount,
                    description=s.fee_type.description,
                )
        return challan

    @classmethod
    @transaction.atomic
    def generate_monthly_challans_for_class(
        cls, school_class_id, month_label, academic_year=None, user=None,
    ) -> int:
        students = Student.objects.filter(
            current_class_id=school_class_id, status=Student.Status.ACTIVE
        )
        count = 0
        for student in students:
            try:
                cls.generate_monthly_challan(student, month_label, academic_year, user)
                count += 1
            except Exception:
                continue
        return count

    # -------------------------------------------------------------------
    # Admission challan
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def generate_admission_challan(cls, admission, fee_type, user=None) -> FeeChallan:
        academic_year = admission.academic_year
        student, _ = cls._ensure_student_exists(admission), False
        # We use the admission data even before the student record is created
        challan = FeeChallan.objects.create(
            challan_no=ChallanNumberService.generate(),
            student=admission.student,  # may be None at this point — set later
            academic_year=academic_year,
            month=f"Admission {admission.academic_year.name}",
            due_date=timezone.now().date() + timedelta(days=settings.SCHOOL_LATE_FEE_DAYS),
            status=FeeChallan.Status.UNPAID,
            is_admission_challan=True,
            created_by=user,
        )
        FeeChallanItem.objects.create(
            challan=challan, fee_type=fee_type, amount=fee_type.default_amount,
        )
        return challan

    @staticmethod
    def _ensure_student_exists(admission):
        return admission.student

    # -------------------------------------------------------------------
    # Payment recording — transaction-safe, duplicate prevention
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def record_payment(
        cls,
        challan: FeeChallan,
        amount: Decimal,
        method: str,
        user=None,
        transaction_ref: str = "",
        payment_date: date = None,
        is_successful: bool = True,
        notes: str = "",
    ) -> FeePayment:
        # Lock the challan row to prevent duplicate concurrent payments
        challan = FeeChallan.objects.select_for_update().get(pk=challan.pk)

        if challan.status == FeeChallan.Status.PAID:
            raise ValueError("Challan is already fully paid.")

        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        # Server-side payment verification should go here in production
        # — never trust client success. For demo we trust is_successful.
        payment = FeePayment.objects.create(
            challan=challan,
            amount=amount,
            method=method,
            transaction_ref=transaction_ref,
            is_successful=is_successful,
            recorded_by=user,
            payment_date=payment_date or timezone.now().date(),
            notes=notes,
        )

        cls.update_challan_status(challan)
        return payment

    # -------------------------------------------------------------------
    # Challan status — derived from successful payments
    # -------------------------------------------------------------------
    @classmethod
    def update_challan_status(cls, challan: FeeChallan) -> FeeChallan:
        challan.refresh_from_db()
        total_paid = challan.total_paid
        total_payable = challan.total_payable

        if total_paid >= total_payable and total_payable > 0:
            challan.status = FeeChallan.Status.PAID
        elif total_paid > 0:
            challan.status = FeeChallan.Status.PARTIAL
        elif challan.due_date and timezone.now().date() > challan.due_date:
            challan.status = FeeChallan.Status.OVERDUE
        else:
            challan.status = FeeChallan.Status.UNPAID
        challan.save(update_fields=["status"])
        return challan

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------
    @staticmethod
    def _due_date_for_month(month_label: str) -> date:
        """month_label e.g. 'October 2026' → first weekday after 15th of that month."""
        try:
            from dateutil.parser import parse
            d = parse(month_label, default=timezone.now().date())
            due = date(d.year, d.month, 15) + timedelta(days=settings.SCHOOL_LATE_FEE_DAYS)
            return due
        except Exception:
            return timezone.now().date() + timedelta(days=15)
