"""Tests for fee service — challan generation, payment, paid stamp logic."""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.common.models import AcademicYear, SchoolClass, Section
from apps.students.models import Student
from apps.fees.models import FeeType, FeeChallan, FeeChallanItem, FeePayment
from apps.fees.services import FeeService

User = get_user_model()


class FeeServiceTest(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name="2026-2027", start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31), is_active=True,
        )
        self.cls = SchoolClass.objects.create(name="Grade 8", grade_level="middle", order=1)
        self.section = Section.objects.create(school_class=self.cls, name="A")
        self.tuition = FeeType.objects.create(
            name="Tuition Fee", code="TUI", fee_type="tuition", default_amount=8000
        )
        # FeeStructure
        from apps.fees.models import FeeStructure
        FeeStructure.objects.create(
            academic_year=self.year, school_class=self.cls,
            fee_type=self.tuition, amount=8000,
        )
        self.student = Student.objects.create(
            registration_no="SCH-2026-000001", full_name="Test Student",
            current_class=self.cls, current_section=self.section,
            status=Student.Status.ACTIVE,
        )
        self.user = User.objects.create_user(username="test", password="test")

    def test_monthly_challan_generation_creates_items(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        self.assertEqual(challan.items.count(), 1)
        self.assertEqual(challan.items.first().fee_type, self.tuition)
        self.assertEqual(challan.total_amount, Decimal("8000"))
        self.assertEqual(challan.status, FeeChallan.Status.UNPAID)

    def test_monthly_challan_is_idempotent(self):
        ch1 = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        ch2 = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        self.assertEqual(ch1.pk, ch2.pk)

    def test_payment_marks_challan_paid(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        payment = FeeService.record_payment(challan, challan.total_payable, "cash", self.user)
        challan.refresh_from_db()
        self.assertEqual(challan.status, FeeChallan.Status.PAID)
        self.assertEqual(challan.total_paid, payment.amount)
        self.assertTrue(payment.is_successful)
        self.assertIsNotNone(payment.receipt_no)

    def test_partial_payment_status(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        FeeService.record_payment(challan, Decimal("3000"), "cash", self.user)
        challan.refresh_from_db()
        self.assertEqual(challan.status, FeeChallan.Status.PARTIAL)
        self.assertEqual(challan.balance, Decimal("5000"))

    def test_duplicate_payment_prevention(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        FeeService.record_payment(challan, challan.total_payable, "cash", self.user)
        challan.refresh_from_db()
        # Trying to pay again should fail
        with self.assertRaises(Exception):
            FeeService.record_payment(challan, Decimal("100"), "cash", self.user)

    def test_late_fee_zero_when_not_overdue(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        challan.due_date = date.today() + timedelta(days=30)
        challan.save()
        self.assertEqual(FeeService.calculate_late_fee(challan), Decimal("0"))

    def test_late_fee_applied_when_overdue(self):
        challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year, self.user)
        challan.due_date = date.today() - timedelta(days=30)
        challan.save()
        self.assertGreater(FeeService.calculate_late_fee(challan), Decimal("0"))
