"""Tests for the payment gateway abstraction layer."""
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from apps.common.models import AcademicYear, SchoolClass, Section
from apps.students.models import Student
from apps.fees.models import FeeChallan, FeeChallanItem, FeeType, FeeStructure
from apps.fees.services import FeeService
from apps.fees.payment_gateway import (
    PaymentGateway, TestGateway, get_gateway, PaymentGatewayError,
)

User = get_user_model()


class PaymentGatewayTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
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
            registration_no="SCH-2026-000001", full_name="Test Student",
            current_class=self.cls, current_section=self.section,
            status=Student.Status.ACTIVE,
        )
        self.challan = FeeService.generate_monthly_challan(self.student, "October 2026", self.year)
        self.user = User.objects.create_user(username="student", password="x", role="student")

    def test_get_gateway_test(self):
        gateway = get_gateway("test")
        self.assertIsInstance(gateway, TestGateway)
        self.assertEqual(gateway.name, "test")

    def test_get_gateway_unknown_raises(self):
        with self.assertRaises(PaymentGatewayError):
            get_gateway("nonexistent_gateway")

    def test_test_gateway_create_checkout(self):
        gateway = get_gateway("test")
        request = self.rf.get("/fees/challans/1/pay/")
        result = gateway.create_checkout(self.challan, request)
        self.assertIn("checkout_url", result)
        self.assertIn("session_id", result)
        self.assertEqual(result["gateway"], "test")
        self.assertTrue(result["session_id"].startswith(f"TEST-{self.challan.challan_no}-"))

    def test_test_gateway_verify_valid_session(self):
        gateway = get_gateway("test")
        request = self.rf.post("/", {
            "session_id": f"TEST-{self.challan.challan_no}-12345",
            "challan_no": self.challan.challan_no,
        })
        is_successful, meta = gateway.verify_payment(request)
        self.assertTrue(is_successful)
        self.assertEqual(meta["challan_no"], self.challan.challan_no)

    def test_test_gateway_verify_invalid_session(self):
        """An attacker tries to fake a session ID — must be rejected."""
        gateway = get_gateway("test")
        request = self.rf.post("/", {
            "session_id": "FAKE-12345",
            "challan_no": self.challan.challan_no,
        })
        is_successful, meta = gateway.verify_payment(request)
        self.assertFalse(is_successful)

    def test_test_gateway_verify_missing_fields(self):
        gateway = get_gateway("test")
        request = self.rf.post("/", {})
        is_successful, meta = gateway.verify_payment(request)
        self.assertFalse(is_successful)

    def test_amount_in_minor_units(self):
        """PKR 8500 → 850000 paisa."""
        self.assertEqual(PaymentGateway.amount_in_minor_units(Decimal("8500.00")), 850000)

    def test_get_challan_by_no(self):
        """Helper looks up challan by challan_no."""
        found = PaymentGateway.get_challan_by_no(self.challan.challan_no)
        self.assertEqual(found.pk, self.challan.pk)
        missing = PaymentGateway.get_challan_by_no("DOES-NOT-EXIST")
        self.assertIsNone(missing)

    def test_full_test_gateway_flow_marks_challan_paid(self):
        """End-to-end: create checkout → verify → record payment → challan PAID."""
        gateway = get_gateway("test")
        request = self.rf.post("/", {
            "session_id": f"TEST-{self.challan.challan_no}-12345",
            "challan_no": self.challan.challan_no,
        })
        is_successful, meta = gateway.verify_payment(request)
        self.assertTrue(is_successful)
        # Simulate webhook handler calling record_payment
        payment = FeeService.record_payment(
            challan=self.challan,
            amount=self.challan.total_payable,
            method=meta["method"],
            user=None,
            transaction_ref=meta["transaction_ref"],
            is_successful=True,
        )
        self.challan.refresh_from_db()
        self.assertEqual(self.challan.status, FeeChallan.Status.PAID)
        self.assertEqual(payment.transaction_ref, meta["transaction_ref"])

    def test_stripe_gateway_raises_without_config(self):
        """StripeGateway must refuse to instantiate without STRIPE_SECRET_KEY."""
        from apps.fees.payment_gateway import StripeGateway
        with self.assertRaises(PaymentGatewayError):
            StripeGateway()

    def test_jazzcash_gateway_raises_without_config(self):
        """JazzCashGateway must refuse to instantiate without credentials."""
        from apps.fees.payment_gateway import JazzCashGateway
        with self.assertRaises(PaymentGatewayError):
            JazzCashGateway()

    def test_jazzcash_secure_hash(self):
        """JazzCashGateway's secure hash uses MD5(salt + sorted values)."""
        from apps.fees.payment_gateway import JazzCashGateway
        # Manually construct without __init__ validation
        gw = JazzCashGateway.__new__(JazzCashGateway)
        gw.salt = "ABCDEF0123456789"
        result = gw._secure_hash(["val1", "val2", "val3"])
        self.assertEqual(len(result), 32)  # MD5 hex digest is 32 chars
