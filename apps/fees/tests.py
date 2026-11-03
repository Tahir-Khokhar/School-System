
"""
Tests for FeeService — challan generation, payments,
partial payments, duplicate prevention, and late fees.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.common.models import AcademicYear, SchoolClass, Section
from apps.students.models import Student
from apps.fees.models import FeeType, FeeChallan, FeePayment, FeeStructure
from apps.fees.services import FeeService


User = get_user_model()


class FeeServiceTest(TestCase):
    """Test fee generation and payment business logic."""

    def setUp(self):
        # Use Django's configured local date.
        self.today = timezone.localdate()

        # Create an active academic year.
        self.year = AcademicYear.objects.create(
            name="2026-2027",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_active=True,
        )

        # Create school class and section.
        self.cls = SchoolClass.objects.create(
            name="Grade 8",
            grade_level="middle",
            order=1,
        )

        self.section = Section.objects.create(
            school_class=self.cls,
            name="A",
        )

        # Create tuition fee type.
        self.tuition = FeeType.objects.create(
            name="Tuition Fee",
            code="TUI",
            fee_type="tuition",
            default_amount=Decimal("8000.00"),
        )

        # Create fee structure.
        FeeStructure.objects.create(
            academic_year=self.year,
            school_class=self.cls,
            fee_type=self.tuition,
            amount=Decimal("8000.00"),
        )

        # Create student.
        self.student = Student.objects.create(
            registration_no="SCH-2026-000001",
            full_name="Test Student",
            current_class=self.cls,
            current_section=self.section,
            status=Student.Status.ACTIVE,
        )

        # Create test user.
        self.user = User.objects.create_user(
            username="test",
            password="test",
        )

    # --------------------------------------------------
    # HELPER METHODS
    # --------------------------------------------------

    def generate_challan(self, month="October 2026", due_in_days=None):
        """
        Generate a monthly challan.

        Optionally assign a controlled due date to prevent
        payment tests from depending on the current date.
        """

        challan = FeeService.generate_monthly_challan(
            self.student,
            month,
            self.year,
            self.user,
        )

        if due_in_days is not None:
            challan.due_date = (
                self.today + timedelta(days=due_in_days)
            )

            challan.save(update_fields=["due_date"])
            challan.refresh_from_db()

        return challan

    # --------------------------------------------------
    # CHALLAN GENERATION TESTS
    # --------------------------------------------------

    def test_monthly_challan_generation_creates_items(self):
        """Verify monthly challan generation creates fee items."""

        challan = self.generate_challan()

        self.assertEqual(challan.items.count(), 1)

        item = challan.items.first()

        self.assertEqual(item.fee_type, self.tuition)

        self.assertEqual(
            challan.total_amount,
            Decimal("8000.00"),
        )

        self.assertEqual(
            challan.status,
            FeeChallan.Status.UNPAID,
        )

    def test_monthly_challan_is_idempotent(self):
        """Generating the same monthly challan twice must not duplicate it."""

        first_challan = self.generate_challan()

        second_challan = self.generate_challan()

        self.assertEqual(
            first_challan.pk,
            second_challan.pk,
        )

        self.assertEqual(
            FeeChallan.objects.filter(
                student=self.student,
                month="October 2026",
                academic_year=self.year,
            ).count(),
            1,
        )

    # --------------------------------------------------
    # PAYMENT TESTS
    # --------------------------------------------------

    def test_payment_marks_challan_paid(self):
        """A full successful payment must mark the challan as paid."""

        challan = self.generate_challan(due_in_days=30)

        payment = FeeService.record_payment(
            challan,
            challan.total_payable,
            "cash",
            self.user,
        )

        challan.refresh_from_db()

        self.assertEqual(
            challan.status,
            FeeChallan.Status.PAID,
        )

        self.assertEqual(
            challan.total_paid,
            payment.amount,
        )

        self.assertTrue(payment.is_successful)

        self.assertTrue(payment.receipt_no)

        self.assertEqual(
            FeePayment.objects.filter(challan=challan).count(),
            1,
        )

    def test_partial_payment_status(self):
        """A partial payment must leave an outstanding balance."""

        challan = self.generate_challan(due_in_days=30)

        payment = FeeService.record_payment(
            challan,
            Decimal("3000.00"),
            "cash",
            self.user,
        )

        challan.refresh_from_db()

        self.assertTrue(payment.is_successful)

        self.assertEqual(
            challan.status,
            FeeChallan.Status.PARTIAL,
        )

        self.assertEqual(
            challan.total_paid,
            Decimal("3000.00"),
        )

        self.assertEqual(
            challan.balance,
            Decimal("5000.00"),
        )

    def test_duplicate_payment_prevention(self):
        """A fully paid challan must reject another payment."""

        challan = self.generate_challan(due_in_days=30)

        first_payment = FeeService.record_payment(
            challan,
            challan.total_payable,
            "cash",
            self.user,
        )

        challan.refresh_from_db()

        self.assertTrue(first_payment.is_successful)

        # A duplicate payment should raise a business validation error.
        with self.assertRaises((ValidationError, ValueError)):
            FeeService.record_payment(
                challan,
                Decimal("100.00"),
                "cash",
                self.user,
            )

        # Verify that no second payment was recorded.
        self.assertEqual(
            FeePayment.objects.filter(challan=challan).count(),
            1,
        )

    # --------------------------------------------------
    # LATE FEE TESTS
    # --------------------------------------------------

    def test_late_fee_zero_when_not_overdue(self):
        """A future due date must not generate a late fee."""

        challan = self.generate_challan(due_in_days=30)

        late_fee = FeeService.calculate_late_fee(challan)

        self.assertEqual(
            late_fee,
            Decimal("0.00"),
        )

    def test_late_fee_applied_when_overdue(self):
        """An overdue challan must receive the configured late fee."""

        challan = self.generate_challan(due_in_days=-30)

        late_fee = FeeService.calculate_late_fee(challan)

        self.assertGreater(
            late_fee,
            Decimal("0.00"),
        )
