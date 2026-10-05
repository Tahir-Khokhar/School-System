"""Tests for payroll service."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.teachers.models import Teacher
from apps.payroll.models import Payroll, PayrollService, SalaryPayment

User = get_user_model()


class PayrollServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hr", password="x", role="hr_payroll")
        self.teacher = Teacher.objects.create(
            employee_id="EMP-0001", full_name="Test Teacher",
            basic_salary=Decimal("50000"), status=Teacher.Status.ACTIVE,
        )

    def test_calculate_salary(self):
        data = PayrollService.calculate_salary(
            self.teacher, "October 2026",
            allowances=Decimal("5000"), deductions=Decimal("2000"),
        )
        self.assertEqual(data["net_salary"], Decimal("53000"))

    def test_generate_payroll_creates_record(self):
        payroll = PayrollService.generate_payroll(self.teacher, "November 2026", self.user)
        self.assertEqual(payroll.teacher, self.teacher)
        self.assertEqual(payroll.month, "November 2026")
        self.assertEqual(payroll.status, Payroll.Status.DRAFT)

    def test_record_bank_payment_marks_paid(self):
        payroll = PayrollService.generate_payroll(self.teacher, "December 2026", self.user)
        payment = PayrollService.record_bank_payment(payroll, self.user)
        payroll.refresh_from_db()
        self.assertEqual(payroll.status, Payroll.Status.PAID)
        self.assertEqual(payment.amount, payroll.net_salary)

    def test_salary_calculation_with_bonus(self):
        data = PayrollService.calculate_salary(
            self.teacher, "October 2026",
            allowances=Decimal("5000"), bonus=Decimal("10000"), deductions=Decimal("2000"),
        )
        self.assertEqual(data["net_salary"], Decimal("63000"))
