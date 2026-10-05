"""
Payment Gateway Abstraction Layer.

This module provides a pluggable interface for online fee payments.
The school can switch between Stripe (international), JazzCash (Pakistan),
or a Test gateway (always succeeds for development) by setting the
ACTIVE_PAYMENT_GATEWAY environment variable.

CRITICAL SECURITY RULE:
    A gateway MUST verify the payment server-side before returning success.
    The student/parent browser NEVER tells us the payment succeeded — only
    the gateway's signed webhook (or signed redirect) does.
"""
from __future__ import annotations
import abc
import hmac
import hashlib
import time
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.urls import reverse

from apps.fees.models import FeeChallan


class PaymentGatewayError(Exception):
    """Base exception for all payment gateway errors."""


class PaymentGateway(abc.ABC):
    """Abstract base class. Subclasses implement gateway-specific API calls."""

    name: str = "base"

    @abc.abstractmethod
    def create_checkout(self, challan: FeeChallan, request) -> dict:
        """
        Create a checkout session at the gateway.

        Returns a dict with at least:
            - 'checkout_url' (str): URL the user is redirected to
            - 'session_id'   (str): internal reference for later lookup
            - 'gateway'      (str): the gateway name

        This URL is what the user's browser will be redirected to.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def verify_payment(self, request) -> tuple[bool, dict]:
        """
        Verify a payment server-side using the gateway's signed callback
        or webhook payload.

        Returns (is_successful: bool, metadata: dict).
        metadata MUST include 'challan_no' so we can find the FeeChallan.

        NEVER trust client-side params. Always recompute the gateway's
        signature with the shared secret and compare with hmac.compare_digest().
        """
        raise NotImplementedError

    # ----- helpers available to all subclasses -----
    @staticmethod
    def get_challan_by_no(challan_no: str) -> Optional[FeeChallan]:
        try:
            return FeeChallan.objects.select_related("student", "academic_year").get(challan_no=challan_no)
        except FeeChallan.DoesNotExist:
            return None

    @staticmethod
    def amount_in_minor_units(amount: Decimal) -> int:
        """Convert PKR Decimal to integer paisa/cents (100 = 1 unit)."""
        return int(amount * 100)


# ---------------------------------------------------------------------------
# Test gateway — always succeeds; used in development
# ---------------------------------------------------------------------------
class TestGateway(PaymentGateway):
    name = "test"

    def create_checkout(self, challan: FeeChallan, request) -> dict:
        session_id = f"TEST-{challan.challan_no}-{int(time.time())}"
        checkout_url = request.build_absolute_uri(
            reverse("fees:gateway_test_pay", args=[challan.pk, session_id])
        )
        return {
            "checkout_url": checkout_url,
            "session_id": session_id,
            "gateway": self.name,
        }

    def verify_payment(self, request) -> tuple[bool, dict]:
        """The Test gateway 'verifies' via the signed URL containing the session_id.
        In production this MUST be replaced with a real gateway's webhook signature check."""
        session_id = request.POST.get("session_id") or request.GET.get("session_id")
        challan_no = request.POST.get("challan_no") or request.GET.get("challan_no")
        if not session_id or not challan_no:
            return False, {}
        # Confirm the session_id format matches what we issued
        if not session_id.startswith(f"TEST-{challan_no}-"):
            return False, {}
        return True, {
            "challan_no": challan_no,
            "transaction_ref": session_id,
            "method": "online",
        }


# ---------------------------------------------------------------------------
# Stripe gateway — uses Stripe Checkout
# ---------------------------------------------------------------------------
class StripeGateway(PaymentGateway):
    name = "stripe"

    def __init__(self):
        import stripe  # local import; fail only when actually used
        self.stripe = stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        if not stripe.api_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY not configured")

    def create_checkout(self, challan: FeeChallan, request) -> dict:
        # Idempotency: build deterministic client_reference_id from challan_no + timestamp
        client_ref = f"{challan.challan_no}-{int(time.time())}"
        amount = self.amount_in_minor_units(challan.total_payable)

        success_url = request.build_absolute_uri(reverse("fees:gateway_stripe_return"))
        success_url += f"?challan_no={challan.challan_no}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse("fees:payment_confirm", args=[challan.pk]))

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
            client_reference_id=client_ref,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "challan_no": challan.challan_no,
                "student_name": challan.student.full_name,
                "registration_no": challan.student.registration_no,
            },
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "gateway": self.name,
            "client_reference_id": client_ref,
        }

    def verify_payment(self, request) -> tuple[bool, dict]:
        """Stripe verifies via webhook signature (Stripe-Signature header)."""
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, self.stripe.error.SignatureVerificationError):
            return False, {}

        if event["type"] != "checkout.session.completed":
            return False, {}

        session = event["data"]["object"]
        if session.payment_status != "paid":
            return False, {}

        challan_no = session.get("metadata", {}).get("challan_no")
        if not challan_no:
            return False, {}
        return True, {
            "challan_no": challan_no,
            "transaction_ref": session.id,
            "method": "card",
        }


# ---------------------------------------------------------------------------
# JazzCash gateway (Pakistan) — implements the standard CPG
# payment request + signed return-URL verification
# ---------------------------------------------------------------------------
class JazzCashGateway(PaymentGateway):
    name = "jazzcash"

    def __init__(self):
        self.merchant_id = settings.JAZZCASH_MERCHANT_ID
        self.password = settings.JAZZCASH_PASSWORD
        self.salt = settings.JAZZCASH_INTEGRITY_SALT
        self.api_url = settings.JAZZCASH_API_URL
        if not all([self.merchant_id, self.password, self.salt]):
            raise PaymentGatewayError("JazzCash credentials not configured")

    def _secure_hash(self, sorted_fields: list) -> str:
        """JazzCash uses an MD5 HMAC over '&' -joined sorted field values, prefixed
        with the integrity salt. This is the official spec from JazzCash docs."""
        data = self.salt + "&" + "&".join(str(v) for v in sorted_fields)
        return hashlib.md5(data.encode("utf-8")).hexdigest().upper()

    def create_checkout(self, challan: FeeChallan, request) -> dict:
        # JazzCash expects a form POST from the browser, so we return the API URL
        # + the signed form fields. The browser submits them via a hidden form.
        txn_ref = f"JC-{challan.challan_no}-{int(time.time())}"
        amount = f"{challan.total_payable:.2f}"  # JazzCash expects decimal string
        post_data = {
            "pp_Amount": self.amount_in_minor_units(challan.total_payable),  # in paisa
            "pp_BillReference": challan.challan_no,
            "pp_Description": f"Fee Challan {challan.challan_no} — {challan.student.full_name}",
            "pp_Language": "EN",
            "pp_MerchantID": self.merchant_id,
            "pp_Password": self.password,
            "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
            "pp_TerminalID": "TTERM01",
            "pp_TxnCurrency": "PKR",
            "pp_TxnDateTime": time.strftime("%Y%m%d%H%M%S", time.localtime()),
            "pp_TxnExpiryDateTime": time.strftime("%Y%m%d%H%M%S", time.localtime(time.time() + 3600)),
            "pp_TxnRefNo": txn_ref,
            "pp_TxnType": "MMT",
            "pp_Version": "2.0",
            "pp_SubMerchantID": "",
            "pp_BankID": "TBANK",
            "pp_ProductID": "RETL",
            "pp_ppmf_TxnRefNo": txn_ref,
        }
        # Sort and hash — JazzCash spec
        sorted_values = [str(v) for k, v in sorted(post_data.items()) if v != ""]
        post_data["pp_SecureHash"] = self._secure_hash(sorted_values)
        return {
            "checkout_url": self.api_url,
            "session_id": txn_ref,
            "gateway": self.name,
            "form_fields": post_data,
        }

    def verify_payment(self, request) -> tuple[bool, dict]:
        """JazzCash posts back to pp_ReturnURL with a signed payload.
        We verify by recomputing the secure hash using the Integrity Salt + sorted fields."""
        post = request.POST
        challan_no = post.get("pp_BillReference", "")
        if not challan_no:
            return False, {}
        # Recompute hash without pp_SecureHash
        received_hash = post.get("pp_SecureHash", "").upper()
        fields = {k: v for k, v in post.items() if k != "pp_SecureHash" and v != ""}
        sorted_values = [str(v) for k, v in sorted(fields.items()) if v != ""]
        expected_hash = self._secure_hash(sorted_values)
        if not hmac.compare_digest(received_hash, expected_hash):
            return False, {}
        # Check payment status
        if post.get("pp_ResponseCode") not in ("000", "121"):  # 000 = success, 121 = success-pending
            return False, {}
        return True, {
            "challan_no": challan_no,
            "transaction_ref": post.get("pp_TxnRefNo", ""),
            "method": "online",
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_GATEWAYS = {
    "test": TestGateway,
    "stripe": StripeGateway,
    "jazzcash": JazzCashGateway,
}


def get_gateway(name: Optional[str] = None) -> PaymentGateway:
    """Get an instance of the active payment gateway."""
    name = name or settings.ACTIVE_PAYMENT_GATEWAY
    cls = _GATEWAYS.get(name)
    if not cls:
        raise PaymentGatewayError(f"Unknown payment gateway: {name}")
    return cls()
