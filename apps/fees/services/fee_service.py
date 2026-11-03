"""FeeService — centralizes school fee business logic.

Responsibilities:
    - Monthly and admission challan generation
    - Late-fee calculation
    - Transaction-safe payment recording
    - Challan status updates

Notes:
    - A monthly challan is idempotent for a student, academic year, and month.
    - Payments are serialized by locking the challan row where the database
      supports SELECT ... FOR UPDATE.
    - A payment is counted toward the balance only when is_successful=True;
      FeeChallan.total_paid is expected to implement that rule.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.common.models import AcademicYear
from apps.students.models import Student

from ..models import (
    ChallanNumberService,
    FeeChallan,
    FeeChallanItem,
    FeePayment,
    FeeStructure,
)


logger = logging.getLogger(__name__)
ZERO = Decimal("0.00")
MAX_CHALLAN_PAYMENT = Decimal("10000000.00")


class FeeService:
    """Business operations for fee challans and payments."""

    # ------------------------------------------------------------------
    # Late fee
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_late_fee(challan: FeeChallan) -> Decimal:
        """Return the applicable flat late fee for ``challan``.

        A previously recorded non-zero ``late_fee_charged`` amount is reused
        for partially paid challans so the amount does not increase repeatedly.
        A fully paid challan returns zero because its payable total already
        includes any late fee recorded at payment time.
        """
        if not challan.due_date:
            return ZERO

        if challan.status == FeeChallan.Status.PAID:
            return ZERO

        recorded_late_fee = Decimal(str(challan.late_fee_charged or ZERO))
        if recorded_late_fee > ZERO:
            return recorded_late_fee

        today = timezone.localdate()
        late_days = (today - challan.due_date).days
        grace_days = int(settings.SCHOOL_LATE_FEE_DAYS)

        if late_days <= grace_days:
            return ZERO

        amount = Decimal(str(settings.SCHOOL_LATE_FEE_AMOUNT))
        if not amount.is_finite() or amount < ZERO:
            raise ValueError("SCHOOL_LATE_FEE_AMOUNT must be a finite, non-negative amount.")

        return amount

    # ------------------------------------------------------------------
    # Monthly challan generation
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def generate_monthly_challan(
        cls,
        student: Student,
        month_label: str,
        academic_year: Optional[AcademicYear] = None,
        user=None,
    ) -> FeeChallan:
        """Generate one monthly challan, returning an existing one if present."""
        if not month_label or not month_label.strip():
            raise ValueError("A valid month label is required.")

        academic_year = academic_year or AcademicYear.objects.get_active()
        if academic_year is None:
            raise ValueError("No active academic year.")

        # Lock the student row so concurrent generation requests for the same
        # student are serialized on databases that support row-level locking.
        student = Student.objects.select_for_update().get(pk=student.pk)

        if not student.current_class:
            raise ValueError(
                f"Student {student.full_name} has no current class assigned."
            )

        due_date = cls._due_date_for_month(month_label)

        existing = FeeChallan.objects.filter(
            student=student,
            academic_year=academic_year,
            month=month_label.strip(),
            is_admission_challan=False,
        ).exclude(status=FeeChallan.Status.CANCELLED).first()

        if existing:
            return existing

        challan = FeeChallan.objects.create(
            challan_no=ChallanNumberService.generate(),
            student=student,
            academic_year=academic_year,
            month=month_label.strip(),
            due_date=due_date,
            status=FeeChallan.Status.UNPAID,
            created_by=user,
        )

        structures = list(
            FeeStructure.objects.filter(
                academic_year=academic_year,
                school_class=student.current_class,
                fee_type__is_active=True,
                applies_monthly=True,
                is_active=True,
            ).select_related("fee_type")
        )

        if not structures:
            # Preserve the project's existing fallback behavior when no
            # monthly fee structure has been configured for the class.
            from ..models import FeeType

            tuition, _ = FeeType.objects.get_or_create(
                code="TUI",
                defaults={
                    "name": "Tuition Fee",
                    "fee_type": "tuition",
                    "default_amount": ZERO,
                },
            )
            FeeChallanItem.objects.create(
                challan=challan,
                fee_type=tuition,
                amount=tuition.default_amount or ZERO,
            )
        else:
            for structure in structures:
                FeeChallanItem.objects.create(
                    challan=challan,
                    fee_type=structure.fee_type,
                    amount=structure.amount,
                    description=structure.fee_type.description,
                )

        return challan

    @classmethod
    def generate_monthly_challans_for_class(
        cls,
        school_class_id,
        month_label,
        academic_year=None,
        user=None,
    ) -> int:
        """Generate monthly challans for active students in a class.

        Each student's generation runs in its own transaction. A failure for
        one student therefore does not leave the transaction unusable or stop
        the remaining students from being processed. The return value is the
        number of students processed successfully (including idempotent hits).
        """
        students = Student.objects.filter(
            current_class_id=school_class_id,
            status=Student.Status.ACTIVE,
        ).order_by("pk")

        processed_count = 0

        for student in students.iterator():
            try:
                # generate_monthly_challan is atomic itself. This try/except
                # surrounds its savepoint so a failed student can be skipped.
                cls.generate_monthly_challan(
                    student=student,
                    month_label=month_label,
                    academic_year=academic_year,
                    user=user,
                )
            except ValueError as exc:
                logger.warning(
                    "Skipping monthly challan for student %s: %s",
                    student.pk,
                    exc,
                )
            except Exception:
                logger.exception(
                    "Failed to generate monthly challan for student %s",
                    student.pk,
                )
            else:
                processed_count += 1

        return processed_count

    # ------------------------------------------------------------------
    # Admission challan
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def generate_admission_challan(cls, admission, fee_type, user=None) -> FeeChallan:
        """Generate an admission challan for an admission linked to a student.

        The current FeeChallan implementation requires a Student relation.
        Therefore the admission must already have a student linked before
        this method is called; this method cannot safely create that Student
        record because the required student fields are not provided here.
        """
        academic_year = getattr(admission, "academic_year", None)
        if academic_year is None:
            raise ValueError("The admission must have an academic year.")

        student = cls._ensure_student_exists(admission)

        if fee_type is None:
            raise ValueError("A fee type is required for an admission challan.")

        month_label = f"Admission {academic_year.name}"

        existing = FeeChallan.objects.filter(
            student=student,
            academic_year=academic_year,
            month=month_label,
            is_admission_challan=True,
        ).exclude(status=FeeChallan.Status.CANCELLED).first()

        if existing:
            return existing

        grace_days = int(settings.SCHOOL_LATE_FEE_DAYS)
        due_date = timezone.localdate() + timedelta(days=grace_days)

        challan = FeeChallan.objects.create(
            challan_no=ChallanNumberService.generate(),
            student=student,
            academic_year=academic_year,
            month=month_label,
            due_date=due_date,
            status=FeeChallan.Status.UNPAID,
            is_admission_challan=True,
            created_by=user,
        )

        FeeChallanItem.objects.create(
            challan=challan,
            fee_type=fee_type,
            amount=fee_type.default_amount or ZERO,
        )

        return challan

    @staticmethod
    def _ensure_student_exists(admission) -> Student:
        """Return the admission's linked student or raise a clear error."""
        student = getattr(admission, "student", None)
        if student is None:
            raise ValueError(
                "The admission must be linked to a student before an "
                "admission challan can be generated."
            )
        return student

    # ------------------------------------------------------------------
    # Payment recording
    # ------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def record_payment(
        cls,
        challan: FeeChallan,
        amount: Decimal,
        method: str,
        user=None,
        transaction_ref: str = "",
        payment_date: Optional[date] = None,
        is_successful: bool = True,
        notes: str = "",
    ) -> FeePayment:
        """Record a payment while preventing overpayment and concurrent races."""
        # Serialize payment attempts against this challan on databases that
        # support SELECT FOR UPDATE (for example PostgreSQL).
        challan = FeeChallan.objects.select_for_update().get(pk=challan.pk)

        if challan.status == FeeChallan.Status.CANCELLED:
            raise ValueError("Cannot pay a cancelled challan.")

        if challan.status == FeeChallan.Status.PAID:
            raise ValueError("Challan is already fully paid.")

        try:
            # str() avoids importing the binary approximation of a float.
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError(f"Invalid payment amount: {amount!r}") from exc

        if not amount.is_finite():
            raise ValueError("Payment amount must be a finite number.")

        if amount <= ZERO:
            raise ValueError("Payment amount must be positive.")

        if amount > MAX_CHALLAN_PAYMENT:
            raise ValueError(
                "Payment amount exceeds the maximum allowed per challan."
            )

        if challan.total_payable <= ZERO:
            raise ValueError("Cannot record payment on a zero-amount challan.")

        # Apply and store a non-zero late fee before checking the outstanding
        # balance. Do this only for successful payments: failed gateway/payment
        # attempts must not alter the amount owed.
        if is_successful and not challan.late_fee_charged:
            current_late_fee = cls.calculate_late_fee(challan)
            if current_late_fee > ZERO:
                challan.late_fee_charged = current_late_fee
                challan.save(update_fields=["late_fee_charged"])
                challan.refresh_from_db()

        balance = challan.balance
        if amount > balance:
            raise ValueError(
                f"Payment amount ({amount}) exceeds outstanding balance ({balance})."
            )

        payment = FeePayment.objects.create(
            challan=challan,
            amount=amount,
            method=method,
            transaction_ref=transaction_ref,
            is_successful=is_successful,
            recorded_by=user,
            payment_date=payment_date or timezone.localdate(),
            notes=notes,
        )

        cls.update_challan_status(challan)
        return payment

    # ------------------------------------------------------------------
    # Challan status
    # ------------------------------------------------------------------
    @classmethod
    def update_challan_status(cls, challan: FeeChallan) -> FeeChallan:
        """Recalculate and persist the challan status from its balances."""
        challan.refresh_from_db()

        total_paid = challan.total_paid
        total_payable = challan.total_payable

        if total_payable <= ZERO:
            # A zero-value challan requires no collection.
            challan.status = FeeChallan.Status.PAID
        elif total_paid >= total_payable:
            challan.status = FeeChallan.Status.PAID
        elif total_paid > ZERO:
            challan.status = FeeChallan.Status.PARTIAL
        elif challan.due_date and timezone.localdate() > challan.due_date:
            challan.status = FeeChallan.Status.OVERDUE
        else:
            challan.status = FeeChallan.Status.UNPAID

        challan.save(update_fields=["status"])
        return challan

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _due_date_for_month(month_label: str) -> date:
        """Return the 15th of the labelled month plus the configured grace days.

        Supported examples: ``October 2026`` and ``Oct 2026``.
        Invalid labels raise ValueError instead of silently assigning a
        potentially incorrect due date based on today's date.
        """
        if not isinstance(month_label, str) or not month_label.strip():
            raise ValueError("A valid month label is required.")

        month_date = None
        for date_format in ("%B %Y", "%b %Y"):
            try:
                month_date = datetime.strptime(
                    month_label.strip(), date_format
                ).date()
                break
            except ValueError:
                continue

        if month_date is None:
            raise ValueError(
                f"Invalid month label {month_label!r}. "
                "Use a format such as 'October 2026'."
            )

        grace_days = int(settings.SCHOOL_LATE_FEE_DAYS)
        if grace_days < 0:
            raise ValueError("SCHOOL_LATE_FEE_DAYS cannot be negative.")

        return date(month_date.year, month_date.month, 15) + timedelta(
            days=grace_days
        )
