"""
Fees app views — challans, lookup, payment, defaulters, PDFs, gateway integration.
"""
import logging
from decimal import Decimal
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q, Sum, F
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView, DetailView, CreateView, FormView, View, TemplateView,
)

from django_ratelimit.decorators import ratelimit

from apps.accounts.mixins import StaffRequiredMixin
from apps.accounts.views import TwoFactorRequiredMixin, rate_limit_exceeded
from apps.students.models import Student
from apps.common.models import AcademicYear, SchoolClass
from .models import (
    FeeChallan, FeeChallanItem, FeePayment, FeeType, FeeStructure,
)
from .forms import (
    FeeTypeForm, FeeStructureForm, ChallanLookupForm, PaymentForm,
    MonthlyChallanGenerateForm,
)
from .services import FeeService
from .payment_gateway import get_gateway, PaymentGatewayError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared rate-limit helpers.
#
# We use `block=False` everywhere so that `request.limited` is set and we can
# render a friendly page instead of Django-ratelimit's bare 403. Each view
# that needs rate limiting overrides `post()` and checks `_is_rate_limited()`.
# ---------------------------------------------------------------------------
def _is_rate_limited(request):
    return getattr(request, "limited", False)


def _rate_limited_response(request):
    return rate_limit_exceeded(request)


# ---------------------------------------------------------------------------
# Fee Types & Structures
# ---------------------------------------------------------------------------
class FeeTypeListView(LoginRequiredMixin, ListView):
    model = FeeType
    template_name = "fees/fee_type_list.html"
    context_object_name = "fee_types"


class FeeTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeeType
    form_class = FeeTypeForm
    template_name = "fees/fee_type_form.html"
    permission_required = "fees.add_feetype"
    success_url = "/fees/fee-types/"


class FeeStructureListView(LoginRequiredMixin, ListView):
    model = FeeStructure
    template_name = "fees/structure_list.html"
    context_object_name = "structures"


class FeeStructureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = "fees/structure_form.html"
    permission_required = "fees.add_feestructure"
    success_url = "/fees/structures/"


# ---------------------------------------------------------------------------
# Challan List / Detail / Generate / Print / PDF
# ---------------------------------------------------------------------------
class FeeChallanListView(StaffRequiredMixin, ListView):
    model = FeeChallan
    template_name = "fees/challan_list.html"
    context_object_name = "challans"
    paginate_by = 25

    def get_queryset(self):
        qs = FeeChallan.objects.select_related(
            "student", "academic_year", "student__current_class"
        )
        status = self.request.GET.get("status")
        if status and status in FeeChallan.Status.values:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            # Use Q() rather than `qs.filter(...) | qs.filter(...)` — the `|`
            # operator drops select_related and can produce UNION-style rows.
            qs = qs.filter(
                Q(challan_no__icontains=q)
                | Q(student__full_name__icontains=q)
                | Q(student__registration_no__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = FeeChallan.Status.choices
        ctx["breadcrumbs"] = [{"title": "Fee Challans"}]
        return ctx


class FeeChallanDetailView(StaffRequiredMixin, DetailView):
    model = FeeChallan
    template_name = "fees/challan_detail.html"
    context_object_name = "challan"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Fee Challans", "url": reverse("fees:challan_list")},
            {"title": self.object.challan_no},
        ]
        ctx["items"] = self.object.items.select_related("fee_type")
        ctx["payments"] = self.object.payments.order_by("-payment_date")
        return ctx


# Shared context builder so HTML and PDF views never diverge.
def build_challan_print_context(challan, request):
    """Build the full context for the 3-copy challan voucher (HTML or PDF)."""
    items = challan.items.select_related("fee_type")
    items_by_type = {item.fee_type.fee_type: item for item in items}

    def amount_for(*fee_types):
        total = Decimal("0")
        for ft in fee_types:
            if ft in items_by_type:
                total += items_by_type[ft].amount
        return total

    late_fee = FeeService.calculate_late_fee(challan)

    fee_rows = [
        {"label": "Security Fees",        "amount": amount_for("security")},
        {"label": "Admission Fees",       "amount": amount_for("admission")},
        {"label": "Development Fund",     "amount": amount_for("annual")},
        {"label": "Tuition Fees",         "amount": amount_for("tuition")},
        {"label": "Misc. Fees",           "amount": amount_for(
            "examination", "lab", "library", "sports", "computer")},
        {"label": "Registration Fees",    "amount": Decimal("0")},
        {"label": "Other",                "amount": Decimal("0")},
        {"label": "Student Card",         "amount": Decimal("0")},
        {"label": "Prospectus Charges",   "amount": Decimal("0")},
        {"label": "Reg. Form Charges",    "amount": Decimal("0")},
        {"label": "Transport Charges",    "amount": amount_for("transport")},
        {"label": "Arrears",              "amount": Decimal("0")},
    ]

    ctx = {
        "challan": challan,
        "items": items,
        "payments": challan.payments.filter(is_successful=True),
        "fee_rows": fee_rows,
        "total_after_due": challan.total_payable + late_fee,
        "copy_labels": ["Bank", "School", "Student"],
        "qr_svg": None,
    }

    # QR code is optional — missing dependency must not 500 the page.
    try:
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        qr_data = (
            f"APS|{challan.challan_no}|"
            f"{challan.student.registration_no}|{challan.total_payable}"
        )
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(qr_data, image_factory=factory, box_size=6, border=1)
        buf = BytesIO()
        img.save(buf)
        ctx["qr_svg"] = buf.getvalue().decode("utf-8")
    except Exception as exc:
        logger.warning("QR generation failed for %s: %s", challan.challan_no, exc)

    return ctx


class FeeChallanPrintView(StaffRequiredMixin, DetailView):
    """Render the APS-style 3-copy voucher (Bank / School / Student) with QR code."""
    template_name = "fees/challan_print.html"
    context_object_name = "challan"
    model = FeeChallan

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_challan_print_context(self.object, self.request))
        return ctx


class MonthlyChallanGenerateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "fees/challan_generate.html"
    form_class = MonthlyChallanGenerateForm
    permission_required = "fees.add_feechallan"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [
            {"title": "Fee Challans", "url": reverse("fees:challan_list")},
            {"title": "Generate Monthly"},
        ]
        return ctx

    def form_valid(self, form):
        school_class = form.cleaned_data.get("school_class") or self.request.GET.get("class")
        month = form.cleaned_data["month_label"]

        if school_class:
            n = FeeService.generate_monthly_challans_for_class(
                school_class, month, user=self.request.user
            )
            messages.success(self.request, f"Generated {n} challan(s) for {month}.")
        else:
            count_total = 0
            failed = 0
            for student in Student.objects.filter(status=Student.Status.ACTIVE):
                try:
                    FeeService.generate_monthly_challan(student, month, user=self.request.user)
                    count_total += 1
                except Exception as exc:
                    failed += 1
                    logger.warning(
                        "Failed to generate challan for %s: %s",
                        student.registration_no, exc,
                    )
            msg = f"Generated {count_total} challan(s) for {month}."
            if failed:
                messages.warning(
                    self.request, msg + f" {failed} student(s) skipped — check logs."
                )
            else:
                messages.success(self.request, msg)
        return redirect("fees:challan_list")


# ---------------------------------------------------------------------------
# Challan Lookup → Payment workflow
# ---------------------------------------------------------------------------
@method_decorator(
    ratelimit(key="user", rate="10/m", method="POST", block=False),
    name="post",
)
class ChallanLookupView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Enter challan number, get the challan, jump to payment confirmation.
    Rate-limited: 10 lookups/minute per user — protects against challan-number
    enumeration attacks."""
    template_name = "fees/payment_lookup.html"
    form_class = ChallanLookupForm
    permission_required = "fees.add_feepayment"

    def post(self, request, *args, **kwargs):
        if _is_rate_limited(request):
            return _rate_limited_response(request)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Record Payment"}]
        return ctx

    def form_valid(self, form):
        challan_no = form.cleaned_data["challan_no"].strip()
        challan = FeeChallan.objects.filter(challan_no__iexact=challan_no).first()
        if not challan:
            messages.error(self.request, f"No challan found with number {challan_no}.")
            return self.form_invalid(form)
        return redirect("fees:payment_confirm", challan_pk=challan.pk)


@method_decorator(
    ratelimit(key="user", rate="5/m", method="POST", block=False),
    name="post",
)
class PaymentConfirmView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Cash/counter payment.
    Rate-limited: 5 payments/minute per user — protects against fast-click attacks."""
    template_name = "fees/payment_confirm.html"
    form_class = PaymentForm
    permission_required = "fees.add_feepayment"

    def post(self, request, *args, **kwargs):
        if _is_rate_limited(request):
            return _rate_limited_response(request)
        return super().post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.challan = get_object_or_404(FeeChallan, pk=kwargs["challan_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["challan"] = self.challan
        ctx["items"] = self.challan.items.select_related("fee_type")
        ctx["breadcrumbs"] = [
            {"title": "Record Payment", "url": reverse("fees:payment_create")},
            {"title": self.challan.challan_no},
        ]
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["amount"] = float(self.challan.balance)
        initial["payment_date"] = datetime.now().date()
        return initial

    def form_valid(self, form):
        # Payment attempt is isolated from downstream side effects — an
        # admission/notification failure must NOT be reported as "payment failed".
        try:
            payment = FeeService.record_payment(
                challan=self.challan,
                amount=form.cleaned_data["amount"],
                method=form.cleaned_data["method"],
                user=self.request.user,
                transaction_ref=form.cleaned_data["transaction_ref"],
                payment_date=form.cleaned_data["payment_date"],
                notes=form.cleaned_data["notes"],
            )
        except Exception as e:
            logger.exception("Payment recording failed for %s", self.challan.challan_no)
            messages.error(self.request, f"Payment failed: {e}")
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Payment of {payment.amount} recorded. Receipt: {payment.receipt_no}.",
        )

        try:
            self.challan.refresh_from_db()
            from apps.admissions.services import AdmissionService
            admission = self.challan.admissions.first()
            if admission and self.challan.status == FeeChallan.Status.PAID:
                AdmissionService.complete_after_payment(admission, self.request.user)
        except Exception as e:
            logger.warning(
                "Admission completion failed for %s: %s",
                self.challan.challan_no, e,
            )

        return redirect("fees:challan_detail", pk=self.challan.pk)


class FeePaymentListView(StaffRequiredMixin, ListView):
    model = FeePayment
    template_name = "fees/payment_list.html"
    context_object_name = "payments"
    paginate_by = 25

    def get_queryset(self):
        qs = FeePayment.objects.select_related(
            "challan", "challan__student", "recorded_by"
        )
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(receipt_no__icontains=q)
                | Q(challan__student__full_name__icontains=q)
            )
        return qs


# ---------------------------------------------------------------------------
# Defaulter report
# ---------------------------------------------------------------------------
class FeeDefaulterReportView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "fees/defaulter_report.html"
    context_object_name = "challans"
    permission_required = "fees.view_feechallan"
    paginate_by = 25

    STATUSES = [
        FeeChallan.Status.UNPAID,
        FeeChallan.Status.PARTIAL,
        FeeChallan.Status.OVERDUE,
    ]

    def get_queryset(self):
        return (
            FeeChallan.objects
            .filter(status__in=self.STATUSES)
            .select_related("student", "academic_year", "student__current_class")
            .order_by("due_date")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # DB-side aggregate — do not pull every row into Python.
        agg = (
            FeeChallan.objects
            .filter(status__in=self.STATUSES)
            .aggregate(total=Sum(F("total_payable") - F("amount_paid")))
        )
        ctx["total_outstanding"] = agg["total"] or Decimal("0")
        ctx["breadcrumbs"] = [
            {"title": "Finance", "url": reverse("fees:challan_list")},
            {"title": "Fee Defaulters"},
        ]
        return ctx


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------
class FeeChallanPDFView(StaffRequiredMixin, View):
    """Render the challan as a printable PDF via WeasyPrint."""

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        ctx = build_challan_print_context(challan, request)
        ctx["is_pdf"] = True
        html = render_to_string("fees/challan_print.html", ctx, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="challan_{challan.challan_no}.pdf"'
        )
        return response


class ReceiptPDFView(LoginRequiredMixin, View):
    """Staff OR the owning student/parent may download the receipt."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        payment = get_object_or_404(FeePayment, pk=kwargs["pk"])
        is_staff = request.user.is_staff or request.user.has_perm("fees.view_feepayment")
        is_owner = getattr(payment.challan.student, "user_id", None) == request.user.pk
        if not (is_staff or is_owner):
            return HttpResponseNotFound("Receipt not found.")
        self.payment = payment
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        payment = self.payment
        challan = payment.challan
        items = challan.items.select_related("fee_type")
        html = render_to_string("fees/receipt_print.html", {
            "payment": payment, "challan": challan, "items": items,
            "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="receipt_{payment.receipt_no}.pdf"'
        )
        return response


# ===========================================================================
# ONLINE PAYMENT GATEWAY — Student/Parent Portal → Gateway → Webhook
# ===========================================================================
@method_decorator(
    ratelimit(key="user", rate="6/m", method="POST", block=False),
    name="post",
)
class OnlinePaymentStartView(LoginRequiredMixin, View):
    """Student/parent clicks 'Pay Online' → redirect to the gateway."""

    def post(self, request, *args, **kwargs):
        if _is_rate_limited(request):
            return _rate_limited_response(request)

        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])

        # Ownership check — only staff or the owning student may pay.
        is_staff = request.user.is_staff or request.user.has_perm("fees.change_feechallan")
        is_owner = getattr(challan.student, "user_id", None) == request.user.pk
        if not (is_staff or is_owner):
            messages.error(request, "You are not allowed to pay this challan.")
            return redirect("fees:challan_detail", pk=challan.pk)

        if challan.status == FeeChallan.Status.PAID:
            messages.error(request, "This challan is already paid.")
            return redirect("fees:challan_detail", pk=challan.pk)

        try:
            gateway = get_gateway()
            checkout = gateway.create_checkout(challan, request)
        except PaymentGatewayError as e:
            messages.error(request, f"Payment gateway not available: {e}")
            return redirect("fees:challan_detail", pk=challan.pk)
        except Exception as e:
            logger.exception("Checkout start failed for %s", challan.challan_no)
            messages.error(request, f"Could not start checkout: {e}")
            return redirect("fees:challan_detail", pk=challan.pk)

        try:
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(
                user=request.user, action="payment", obj=challan,
                description=(
                    f"Started online payment via {gateway.name} gateway "
                    f"(session {checkout.get('session_id')})"
                ),
            )
        except Exception:
            logger.exception("Audit log failed for checkout start")

        if "form_fields" in checkout:
            return render(request, "fees/gateway_redirect.html", {
                "checkout_url": checkout["checkout_url"],
                "form_fields": checkout["form_fields"],
                "challan": challan,
            })
        return redirect(checkout["checkout_url"])


def _record_online_payment_once(challan, meta, *, user=None, source=""):
    """Idempotent online-payment recording shared by webhook/callback views.

    Returns (payment, created). Raises on unexpected DB errors so the caller
    can decide how to respond to the gateway.
    """
    txn_ref = meta.get("transaction_ref") or ""

    # Idempotency: if this transaction_ref was already recorded, return it.
    if txn_ref:
        existing = FeePayment.objects.filter(
            challan=challan, transaction_ref=txn_ref
        ).first()
        if existing:
            return existing, False

    if challan.status == FeeChallan.Status.PAID:
        return None, False

    payment = FeeService.record_payment(
        challan=challan,
        amount=meta.get("amount", challan.total_payable),
        method=meta.get("method", "online"),
        user=user,
        transaction_ref=txn_ref,
        notes=f"Online payment verified ({source})",
        is_successful=True,
    )
    return payment, True


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Stripe webhook endpoint. Excludes CSRF (Stripe signs its own payloads).
    Verified server-side using STRIPE_WEBHOOK_SECRET."""
    try:
        gateway = get_gateway("stripe")
    except PaymentGatewayError:
        return HttpResponseBadRequest("Stripe not configured")

    try:
        is_successful, meta = gateway.verify_payment(request)
    except Exception:
        logger.exception("Stripe webhook verification raised")
        return HttpResponseBadRequest("Webhook verification failed")

    if not is_successful:
        return HttpResponse("OK (ignored)")

    challan = FeeChallan.objects.filter(challan_no=meta.get("challan_no")).first()
    if not challan:
        logger.warning("Stripe webhook for unknown challan: %s", meta.get("challan_no"))
        return HttpResponseBadRequest("Unknown challan")

    try:
        payment, created = _record_online_payment_once(
            challan, meta, user=None, source="Stripe webhook"
        )
    except Exception:
        # Do NOT swallow: return 5xx so Stripe retries, otherwise the
        # payment is silently lost.
        logger.exception(
            "Stripe webhook: failed to record payment for %s", challan.challan_no
        )
        return HttpResponse("Retry", status=500)

    if created:
        try:
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(
                user=None, action="payment", obj=challan,
                description=(
                    f"Online payment verified via Stripe webhook — "
                    f"{meta.get('transaction_ref')}"
                ),
            )
            from apps.notifications.models import NotificationService
            NotificationService.notify_role(
                "accountant",
                "New Online Fee Payment",
                (
                    f"{challan.student.full_name} paid {challan.total_payable} "
                    f"for {challan.month or challan.challan_no}."
                ),
                "fee_payment",
            )
        except Exception:
            logger.exception(
                "Post-payment side effects failed for %s", challan.challan_no
            )

    return HttpResponse("OK")


@method_decorator(csrf_exempt, name="dispatch")
class JazzCashReturnView(View):
    """JazzCash redirects the browser back here with a signed POST.
    We verify the secure hash server-side BEFORE trusting anything."""

    def post(self, request, *args, **kwargs):
        try:
            gateway = get_gateway("jazzcash")
        except PaymentGatewayError:
            return HttpResponseBadRequest("JazzCash not configured")

        try:
            is_successful, meta = gateway.verify_payment(request)
        except Exception:
            logger.exception("JazzCash secure-hash verification raised")
            return HttpResponseBadRequest("JazzCash verification failed")

        # Only trust challan_no from the verified payload, never from
        # user-controlled POST data (pp_BillReference).
        challan_no = meta.get("challan_no")
        if not challan_no:
            logger.warning("JazzCash callback missing challan_no in verified meta")
            return HttpResponseBadRequest("Missing challan reference")

        challan = FeeChallan.objects.filter(challan_no=challan_no).first()
        if not challan:
            messages.error(request, "Challan not found.")
            return redirect("dashboard:home")

        if is_successful:
            try:
                payment, created = _record_online_payment_once(
                    challan, meta,
                    user=request.user if request.user.is_authenticated else None,
                    source="JazzCash secure hash",
                )
            except Exception:
                logger.exception(
                    "JazzCash: failed to record payment for %s", challan.challan_no
                )
                messages.error(
                    request,
                    "Payment could not be recorded. If you were charged, "
                    "please contact the school office with your transaction ID.",
                )
                return redirect("fees:challan_detail", pk=challan.pk)

            if created:
                messages.success(
                    request,
                    "Payment verified successfully! Your challan is now PAID.",
                )
                try:
                    from apps.audit_logs.models import AuditLogService
                    AuditLogService.log(
                        user=request.user if request.user.is_authenticated else None,
                        action="payment", obj=challan,
                        description=(
                            f"JazzCash payment verified — "
                            f"{meta.get('transaction_ref')}"
                        ),
                    )
                except Exception:
                    logger.exception("Audit log failed for JazzCash payment")
            else:
                messages.info(request, "This payment was already recorded.")
        else:
            messages.error(
                request,
                "Payment verification failed. If you were charged, please "
                "contact the school office.",
            )
        return redirect("fees:challan_detail", pk=challan.pk)


# ---------------------------------------------------------------------------
# Test gateway
# ---------------------------------------------------------------------------
class TestGatewayPayView(LoginRequiredMixin, View):
    """Test gateway 'checkout' — ONLY available when DEBUG=True.

    Requires login, verifies the session_id binds to the challan, charges the
    outstanding balance only.

    Session-id format (matches what the test gateway's create_checkout
    produces): f"test-{challan.challan_no}-{nonce}"

    NOTE: challan numbers themselves contain dashes (e.g. "CH-2026-000123"),
    so splitting the session id on "-" and comparing segment-by-segment is
    wrong — we match the exact expected prefix instead and require a non-empty
    nonce after it.
    """

    def dispatch(self, request, *args, **kwargs):
        from django.conf import settings
        if not settings.DEBUG:
            return HttpResponseNotFound("Test gateway is not available in production.")
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _session_matches(session_id, challan):
        if not session_id:
            return False
        prefix = f"test-{challan.challan_no}-"
        return session_id.startswith(prefix) and len(session_id) > len(prefix)

    def get(self, request, *args, **kwargs):
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        session_id = kwargs["session_id"]
        if not self._session_matches(session_id, challan):
            return HttpResponseBadRequest("Session ID does not match this challan.")
        if challan.status in (FeeChallan.Status.PAID, FeeChallan.Status.CANCELLED):
            messages.error(request, "This challan cannot be paid online.")
            return redirect("fees:challan_detail", pk=challan.pk)
        return render(request, "fees/test_gateway_pay.html", {
            "challan": challan,
            "session_id": session_id,
        })

    def post(self, request, *args, **kwargs):
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        session_id = kwargs.get("session_id", "")
        posted_challan_no = request.POST.get("challan_no", "")

        if not self._session_matches(session_id, challan):
            return HttpResponseBadRequest("Session ID does not match this challan.")
        if posted_challan_no != challan.challan_no:
            messages.error(request, "Challan number mismatch. Payment rejected.")
            return redirect("fees:challan_detail", pk=challan.pk)

        if challan.status == FeeChallan.Status.PAID:
            messages.error(request, "This challan is already paid.")
            return redirect("fees:challan_detail", pk=challan.pk)
        if challan.status == FeeChallan.Status.CANCELLED:
            messages.error(request, "This challan has been cancelled.")
            return redirect("fees:challan_detail", pk=challan.pk)

        try:
            amount_to_charge = challan.balance
            if amount_to_charge <= 0:
                messages.error(request, "No balance due on this challan.")
                return redirect("fees:challan_detail", pk=challan.pk)

            FeeService.record_payment(
                challan=challan,
                amount=amount_to_charge,
                method="online",
                user=request.user,
                transaction_ref=f"TEST-{session_id}",
                notes="Test gateway payment (DEBUG only)",
                is_successful=True,
            )
            messages.success(request, "Test payment recorded. Challan marked PAID.")
        except ValueError as e:
            messages.error(request, f"Payment failed: {e}")
        except Exception:
            logger.exception(
                "Test gateway payment failed for %s", challan.challan_no
            )
            messages.error(request, "Payment error. Please try again.")
        return redirect("fees:challan_detail", pk=challan.pk)


class StripeReturnView(LoginRequiredMixin, View):
    """User is redirected here after a Stripe checkout.
    We do NOT trust this URL — actual verification happens in stripe_webhook.
    We just show a friendly 'processing' page."""

    def get(self, request, *args, **kwargs):
        challan_no = request.GET.get("challan_no")
        challan = FeeChallan.objects.filter(challan_no=challan_no).first()

        # Do not leak challan existence to non-owners.
        if challan:
            is_staff = request.user.is_staff or request.user.has_perm(
                "fees.view_feechallan"
            )
            is_owner = getattr(challan.student, "user_id", None) == request.user.pk
            if not (is_staff or is_owner):
                challan = None

        if challan and challan.status == FeeChallan.Status.PAID:
            messages.success(request, "Payment successful! Your challan is PAID.")
            return redirect("fees:challan_detail", pk=challan.pk)
        return render(request, "fees/payment_processing.html", {"challan": challan})
