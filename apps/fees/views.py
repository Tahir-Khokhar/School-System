"""
Fees app views — challans, lookup, payment, defaulters, PDFs, gateway integration.
"""
import io
from decimal import Decimal
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, FormView, View, TemplateView

from django_ratelimit.decorators import ratelimit

from apps.accounts.views import TwoFactorRequiredMixin
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
class FeeChallanListView(LoginRequiredMixin, ListView):
    model = FeeChallan
    template_name = "fees/challan_list.html"
    context_object_name = "challans"
    paginate_by = 25

    def get_queryset(self):
        qs = FeeChallan.objects.select_related("student", "academic_year", "student__current_class")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(challan_no__icontains=q) | qs.filter(student__full_name__icontains=q) | qs.filter(student__registration_no__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = FeeChallan.Status.choices
        ctx["breadcrumbs"] = [{"title": "Fee Challans"}]
        return ctx


class FeeChallanDetailView(LoginRequiredMixin, DetailView):
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
        ctx["payments"] = self.object.payments.all().order_by("-payment_date")
        return ctx


class FeeChallanPrintView(LoginRequiredMixin, DetailView):
    """Render the APS-style 3-copy voucher (Bank / School / Student) with QR code."""
    template_name = "fees/challan_print.html"
    context_object_name = "challan"
    model = FeeChallan

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("fee_type")
        ctx["payments"] = self.object.payments.filter(is_successful=True)

        # Build 12-row APS-style fee breakdown
        # Maps our internal fee items to APS's standard 12-row format
        items_by_type = {item.fee_type.fee_type: item for item in ctx["items"]}
        def amount_for(*fee_types):
            total = Decimal("0")
            for ft in fee_types:
                if ft in items_by_type:
                    total += items_by_type[ft].amount
            return total

        ctx["fee_rows"] = [
            {"label": "Security Fees",        "amount": amount_for("other") if "security" in str(items_by_type) else Decimal("0")},
            {"label": "Admission Fees",       "amount": amount_for("admission")},
            {"label": "Development Fund",     "amount": amount_for("annual")},
            {"label": "Tuition Fees",         "amount": amount_for("tuition")},
            {"label": "Misc. Fees",           "amount": amount_for("examination", "lab", "library", "sports", "computer")},
            {"label": "Registration Fees",    "amount": Decimal("0")},
            {"label": "Other",                "amount": Decimal("0")},
            {"label": "Student Card",         "amount": Decimal("0")},
            {"label": "Prospectus Charges",   "amount": Decimal("0")},
            {"label": "Reg. Form Charges",    "amount": Decimal("0")},
            {"label": "Transport Charges",    "amount": amount_for("transport")},
            {"label": "Arrears",              "amount": Decimal("0")},
        ]

        # Total after due date = total + late fee
        from apps.fees.services import FeeService
        late_fee = FeeService.calculate_late_fee(self.object)
        ctx["total_after_due"] = self.object.total_payable + late_fee

        # Three copies for Bank / School / Student
        ctx["copy_labels"] = ["Bank", "School", "Student"]

        # Generate QR code SVG (contains challan number + amount for bank scanning)
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr_data = f"APS|{self.object.challan_no}|{self.object.student.registration_no}|{self.object.total_payable}"
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(qr_data, image_factory=factory, box_size=6, border=1)
        buf = BytesIO()
        img.save(buf)
        ctx["qr_svg"] = buf.getvalue().decode("utf-8")

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
        school_class_id = self.request.POST.get("school_class") or self.request.GET.get("class")
        month = form.cleaned_data["month_label"]
        if school_class_id:
            n = FeeService.generate_monthly_challans_for_class(school_class_id, month, user=self.request.user)
            messages.success(self.request, f"Generated {n} challan(s) for {month}.")
        else:
            # generate for all active students
            count_total = 0
            for student in Student.objects.filter(status=Student.Status.ACTIVE):
                try:
                    FeeService.generate_monthly_challan(student, month, user=self.request.user)
                    count_total += 1
                except Exception:
                    continue
            messages.success(self.request, f"Generated {count_total} challan(s) for {month}.")
        return redirect("fees:challan_list")


# ---------------------------------------------------------------------------
# Challan Lookup → Payment workflow
# ---------------------------------------------------------------------------
class ChallanLookupView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Enter challan number, get the challan, jump to payment confirmation.
    Rate-limited: 10 lookups/minute per user — protects against challan-number
    enumeration attacks."""
    template_name = "fees/payment_lookup.html"
    form_class = ChallanLookupForm
    permission_required = "fees.add_feepayment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Record Payment"},
        ]
        return ctx

    def form_valid(self, form):
        from django_ratelimit.decorators import ratelimit
        from django.utils.decorators import method_decorator

        challan_no = form.cleaned_data["challan_no"].strip()
        challan = FeeChallan.objects.filter(challan_no__iexact=challan_no).first()
        if not challan:
            messages.error(self.request, f"No challan found with number {challan_no}.")
            return self.form_invalid(form)
        return redirect("fees:payment_confirm", challan_pk=challan.pk)


@method_decorator(ratelimit(key="user", rate="10/m", method="POST", block=True), name="post")
@method_decorator(ratelimit(key="user", rate="5/m", method="POST", block=True), name="post")
class PaymentConfirmView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Cash/counter payment.
    Rate-limited: 5 payments/minute per user — protects against fast-click attacks."""
    template_name = "fees/payment_confirm.html"
    form_class = PaymentForm
    permission_required = "fees.add_feepayment"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            from apps.accounts.views import rate_limit_exceeded
            return rate_limit_exceeded(request)
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
            messages.success(
                self.request,
                f"Payment of {payment.amount} recorded. Receipt: {payment.receipt_no}."
            )
            # Try to fire admission completion if it was an admission challan
            try:
                from apps.admissions.services import AdmissionService
                admission = self.challan.admissions.first()
                if admission and self.challan.status == FeeChallan.Status.PAID:
                    AdmissionService.complete_after_payment(admission, self.request.user)
            except Exception:
                pass
            return redirect("fees:challan_detail", pk=self.challan.pk)
        except Exception as e:
            messages.error(self.request, f"Payment failed: {e}")
            return self.form_invalid(form)


class FeePaymentListView(LoginRequiredMixin, ListView):
    model = FeePayment
    template_name = "fees/payment_list.html"
    context_object_name = "payments"
    paginate_by = 25

    def get_queryset(self):
        qs = FeePayment.objects.select_related("challan", "challan__student", "recorded_by")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(receipt_no__icontains=q) | qs.filter(challan__student__full_name__icontains=q)
        return qs


# ---------------------------------------------------------------------------
# Defaulter report
# ---------------------------------------------------------------------------
class FeeDefaulterReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "fees/defaulter_report.html"
    context_object_name = "challans"
    permission_required = "fees.view_feechallan"
    paginate_by = 25

    def get_queryset(self):
        return FeeChallan.objects.filter(
            status__in=[FeeChallan.Status.UNPAID, FeeChallan.Status.PARTIAL, FeeChallan.Status.OVERDUE]
        ).select_related("student", "academic_year", "student__current_class").order_by("due_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["total_outstanding"] = sum(c.balance for c in qs)
        ctx["breadcrumbs"] = [
            {"title": "Finance", "url": reverse("fees:challan_list")},
            {"title": "Fee Defaulters"},
        ]
        return ctx


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------
class FeeChallanPDFView(LoginRequiredMixin, View):
    """Render the challan as a printable PDF via WeasyPrint — APS-style 3-copy voucher."""

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        # Reuse the same context-building logic as FeeChallanPrintView
        view = FeeChallanPrintView()
        view.object = challan
        view.request = request
        ctx = view.get_context_data()
        ctx["is_pdf"] = True
        html = render_to_string("fees/challan_print.html", ctx, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="challan_{challan.challan_no}.pdf"'
        return response


class ReceiptPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        payment = get_object_or_404(FeePayment, pk=kwargs["pk"])
        challan = payment.challan
        items = challan.items.select_related("fee_type")
        html = render_to_string("fees/receipt_print.html", {
            "payment": payment, "challan": challan, "items": items,
            "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="receipt_{payment.receipt_no}.pdf"'
        return response


# ===========================================================================
# ONLINE PAYMENT GATEWAY — Student/Parent Portal → Gateway → Webhook
# ===========================================================================
class OnlinePaymentStartView(LoginRequiredMixin, View):
    """Student/parent clicks 'Pay Online' → we redirect to the gateway.
    Rate-limited: 6 checkout starts/minute per user."""

    @method_decorator(ratelimit(key="user", rate="6/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            from apps.accounts.views import rate_limit_exceeded
            return rate_limit_exceeded(request)
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
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
            messages.error(request, f"Could not start checkout: {e}")
            return redirect("fees:challan_detail", pk=challan.pk)

        # Audit the checkout start
        from apps.audit_logs.models import AuditLogService
        AuditLogService.log(
            user=request.user, action="payment",
            obj=challan,
            description=f"Started online payment via {gateway.name} gateway (session {checkout.get('session_id')})",
        )

        # JazzCash returns form fields that need to be POSTed via browser,
        # so render an auto-submit form
        if "form_fields" in checkout:
            return render(request, "fees/gateway_redirect.html", {
                "checkout_url": checkout["checkout_url"],
                "form_fields": checkout["form_fields"],
                "challan": challan,
            })
        # Stripe / Test → simple redirect
        return redirect(checkout["checkout_url"])


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
        return HttpResponseBadRequest("Webhook verification failed")
    if not is_successful:
        return HttpResponse("OK (ignored)")
    challan = FeeChallan.objects.filter(challan_no=meta.get("challan_no")).first()
    if not challan:
        return HttpResponseBadRequest("Unknown challan")
    # Record the payment (transaction-safe, idempotent)
    try:
        if challan.status != FeeChallan.Status.PAID:
            FeeService.record_payment(
                challan=challan,
                amount=challan.total_payable,
                method=meta.get("method", "online"),
                user=None,
                transaction_ref=meta.get("transaction_ref", ""),
                notes="Online payment verified by gateway webhook",
                is_successful=True,
            )
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(
                user=None, action="payment",
                obj=challan,
                description=f"Online payment verified via Stripe webhook — {meta.get('transaction_ref')}",
            )
            # Notify admins
            from apps.notifications.models import NotificationService
            NotificationService.notify_role(
                "accountant",
                "New Online Fee Payment",
                f"{challan.student.full_name} paid {challan.total_payable} for {challan.month or challan.challan_no}.",
                "fee_payment",
            )
    except Exception as e:
        # Likely already-paid (idempotent); log and move on
        pass
    return HttpResponse("OK")


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class JazzCashReturnView(View):
    """JazzCash redirects the browser back here with a signed POST.
    We verify the secure hash server-side BEFORE trusting anything."""

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            from apps.accounts.views import rate_limit_exceeded
            return rate_limit_exceeded(request)
        try:
            gateway = get_gateway("jazzcash")
        except PaymentGatewayError:
            return HttpResponseBadRequest("JazzCash not configured")
        is_successful, meta = gateway.verify_payment(request)
        challan_no = meta.get("challan_no") or request.POST.get("pp_BillReference", "")
        challan = FeeChallan.objects.filter(challan_no=challan_no).first()
        if not challan:
            messages.error(request, "Challan not found.")
            return redirect("dashboard:home")
        if is_successful and challan.status != FeeChallan.Status.PAID:
            FeeService.record_payment(
                challan=challan,
                amount=challan.total_payable,
                method=meta.get("method", "online"),
                user=request.user if request.user.is_authenticated else None,
                transaction_ref=meta.get("transaction_ref", ""),
                notes="Online payment verified by JazzCash secure hash",
                is_successful=True,
            )
            messages.success(request, "Payment verified successfully! Your challan is now PAID.")
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(
                user=request.user if request.user.is_authenticated else None,
                action="payment", obj=challan,
                description=f"JazzCash payment verified — {meta.get('transaction_ref')}",
            )
        else:
            messages.error(request, "Payment verification failed. If you were charged, please contact the school office.")
        return redirect("fees:challan_detail", pk=challan.pk)


class TestGatewayPayView(View):
    """Test gateway 'checkout' — simulates the payment page in development.
    In production this view is NOT mounted (only TestGateway calls it)."""

    def get(self, request, *args, **kwargs):
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        session_id = kwargs["session_id"]
        return render(request, "fees/test_gateway_pay.html", {
            "challan": challan,
            "session_id": session_id,
        })

    def post(self, request, *args, **kwargs):
        # In test mode we always succeed; real gateways verify via webhook.
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        try:
            gateway = get_gateway("test")
            is_successful, meta = gateway.verify_payment(request)
            if is_successful and challan.status != FeeChallan.Status.PAID:
                FeeService.record_payment(
                    challan=challan,
                    amount=challan.total_payable,
                    method=meta.get("method", "online"),
                    user=request.user if request.user.is_authenticated else None,
                    transaction_ref=meta.get("transaction_ref", ""),
                    notes="Test gateway payment",
                    is_successful=True,
                )
                messages.success(request, "Test payment recorded. Challan marked PAID.")
        except Exception as e:
            messages.error(request, f"Test payment failed: {e}")
        return redirect("fees:challan_detail", pk=challan.pk)


class StripeReturnView(View):
    """User is redirected here after a successful Stripe checkout.
    NOTE: We don't trust this URL — the actual payment verification happens
    in the stripe_webhook view. We just show a friendly 'processing' page."""

    def get(self, request, *args, **kwargs):
        challan_no = request.GET.get("challan_no")
        challan = FeeChallan.objects.filter(challan_no=challan_no).first()
        if challan and challan.status == FeeChallan.Status.PAID:
            messages.success(request, "Payment successful! Your challan is PAID.")
            return redirect("fees:challan_detail", pk=challan.pk)
        return render(request, "fees/payment_processing.html", {"challan": challan})
