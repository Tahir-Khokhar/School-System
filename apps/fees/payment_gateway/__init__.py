"""Payment Gateway Abstraction Layer."""
from __future__ import annotations

import abc
import hashlib
import hmac
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, TypedDict

from django.conf import settings
from django.urls import reverse

from apps.fees.models import FeeChallan


class PaymentGatewayError(Exception):
    pass


class PaymentMetadata(TypedDict, total=False):
    challan_no: str
    transaction_ref: str
    method: str
    amount: Decimal


class PaymentGateway(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def create_checkout(self, challan: FeeChallan, request) -> dict: ...

    @abc.abstractmethod
    def verify_payment(self, request) -> tuple[bool, PaymentMetadata]: ...

    @staticmethod
    def get_challan_by_no(challan_no: str) -> Optional[FeeChallan]:
        return (
            FeeChallan.objects
            .select_related("student", "academic_year")
            .filter(challan_no=challan_no)
            .first()
        )

    @staticmethod
    def amount_in_minor_units(amount: Decimal) -> int:
        return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


class TestGateway(PaymentGateway):
    name = "test"

    def __init__(self):
        if not settings.DEBUG and not getattr(settings, "ALLOW_TEST_GATEWAY", False):
            raise PaymentGatewayError(
                "TestGateway is disabled outside DEBUG. "
                "Set ALLOW_TEST_GATEWAY=True to override."
            )

    def create_checkout(self, challan, request):
        session_id = f"TEST-{challan.challan_no}-{int(time.time())}"
        url = request.build_absolute_uri(
            reverse("fees:gateway_test_pay", args=[challan.pk, session_id])
        )
        return {"checkout_url": url, "session_id": session_id, "gateway": self.name}

    def verify_payment(self, request):
        src = request.POST if request.method == "POST" else request.GET
        session_id = src.get("session_id") or ""
        challan_no = src.get("challan_no") or ""
        if not (session_id and challan_no):
            return False, {}
        if not session_id.startswith(f"TEST-{challan_no}-"):
            return False, {}
        challan = self.get_challan_by_no(challan_no)
        if challan is None:
            return False, {}
        return True, {
            "challan_no": challan_no,
            "transaction_ref": session_id,
            "method": "online",
            "amount": challan.balance,
        }

class StripeGateway(PaymentGateway):
    name = "stripe"

    def __init__(self):
        import stripe
        self.stripe = stripe
        stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY not configured")

    def create_checkout(self, challan, request):
        amount = self.amount_in_minor_units(challan.balance)
        if amount <= 0:
            raise PaymentGatewayError("Nothing to pay on this challan.")

        success_url = (
            request.build_absolute_uri(reverse("fees:gateway_stripe_return"))
            + f"?challan_no={challan.challan_no}&session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = request.build_absolute_uri(
            reverse("fees:payment_confirm", args=[challan.pk])
        )
        try:
            session = self.stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "pkr",
                        "product_data": {
                            "name": f"Fee Challan {challan.challan_no}",
                            "description": f"{challan.student.full_name} — {challan.month or 'Admission'}",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                client_reference_id=challan.challan_no,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "challan_no": challan.challan_no,
                    "expected_amount": str(amount),  # lock the amount
                },
                idempotency_key=f"{challan.challan_no}-{amount}-{int(time.time())}",
            )
        except self.stripe.error.StripeError as e:
            raise PaymentGatewayError(f"Stripe error: {e.user_message or e}") from e

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "gateway": self.name,
        }

    def verify_payment(self, request):
        # The webhook view MUST be @csrf_exempt and MUST NOT read request.POST first.
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, self.stripe.error.SignatureVerificationError):
            return False, {}

        if event["type"] != "checkout.session.completed":
            return False, {}
        session = event["data"]["object"]
        if session.get("payment_status") != "paid":
            return False, {}
        if session.get("currency", "").lower() != "pkr":
            return False, {}

        meta = session.get("metadata") or {}
        challan_no = meta.get("challan_no")
        if not challan_no:
            return False, {}

        amount = Decimal(session.get("amount_total") or 0) / 100
        expected = Decimal(meta.get("expected_amount") or 0)
        if expected and amount != expected:
            return False, {}

        return True, {
            "challan_no": challan_no,
            "transaction_ref": session.id,
            "method": "card",
            "amount": amount,
        }
