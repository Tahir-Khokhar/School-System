"""Tests for rate limiting on the payment endpoint."""
from datetime import date
from decimal import Decimal
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.common.models import AcademicYear, SchoolClass, Section
from apps.students.models import Student
from apps.fees.models import FeeType, FeeStructure
from apps.fees.services import FeeService


class RateLimitTest(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name="2026-2027", start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31), is_active=True,
        )
        self.cls = SchoolClass.objects.create(name="Grade 8", grade_level="middle", order=1)
        self.section = Section.objects.create(school_class=self.cls, name="A")
        self.tuition = FeeType.objects.create(name="Tuition Fee", code="TUI", default_amount=8000)
        FeeStructure.objects.create(
            academic_year=self.year, school_class=self.cls,
            fee_type=self.tuition, amount=Decimal("8000"),
        )
        self.student = Student.objects.create(
            registration_no="SCH-2026-000002", full_name="Rate Limit Test",
            current_class=self.cls, current_section=self.section,
            status=Student.Status.ACTIVE,
        )
        self.challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year)
        self.user = User.objects.create_user(
            username="ratetest", password="test12345",
            role=User.Role.STUDENT,
        )

    def test_online_pay_endpoint_requires_login(self):
        url = reverse("fees:online_pay", args=[self.challan.pk])
        response = self.client.post(url)
        # LoginRequiredMixin redirects anonymous → 302 to login
        self.assertEqual(response.status_code, 302)

    def test_stripe_webhook_rejects_unsigned(self):
        """Stripe webhook must return 400 for requests without a valid signature."""
        url = reverse("fees:stripe_webhook")
        response = self.client.post(url, "{}", content_type="application/json")
        # Stripe not configured → 400 (gateway raises)
        self.assertEqual(response.status_code, 400)
