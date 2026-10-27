from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, View, FormView
from django.views.generic.detail import SingleObjectMixin

from apps.teachers.models import Teacher
from .models import Payroll, SalaryPayment, PayrollService
from .forms import PayrollForm, SalaryPaymentForm


PAYROLL_ROLES = {"super_admin", "hr_payroll"}


class PayrollAccessMixin(LoginRequiredMixin):
    """Only HR/Payroll role, payroll-permission holders, or superusers."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (
            user.is_superuser
            or getattr(user, "role", None) in PAYROLL_ROLES
            or user.has_perm("payroll.view_payroll")
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PayrollListView(PayrollAccessMixin, ListView):
    model = Payroll
    template_name = "payroll/payroll_list.html"
    context_object_name = "payrolls"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Payroll.objects.select_related("teacher")
            .order_by("-month", "-id")
        )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(teacher__full_name__icontains=q)
                | Q(teacher__employee_id__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Payroll.Status.choices
        ctx["breadcrumbs"] = [{"title": "Teacher Payroll"}]
        return ctx


class PayrollCreateView(PayrollAccessMixin, CreateView):
    model = Payroll
    form_class = PayrollForm
    template_name = "payroll/payroll_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Teacher Payroll", "url": reverse("payroll:payroll_list")},
            {"title": "New"},
        ]
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        teacher_id = self.request.GET.get("teacher")
        if teacher_id:
            teacher = Teacher.objects.filter(pk=teacher_id).first()
            if teacher:
                initial["teacher"] = teacher.pk
                initial["basic_salary"] = teacher.basic_salary
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Payroll record created.")
        return response

    def get_success_url(self):
        return reverse("payroll:payroll_detail", args=[self.object.pk])


class PayrollDetailView(PayrollAccessMixin, DetailView):
    model = Payroll
    template_name = "payroll/payroll_detail.html"
    context_object_name = "payroll"


class PayrollApproveView(PayrollAccessMixin, SingleObjectMixin, View):
    model = Payroll

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            p = (
                Payroll.objects
                .select_for_update()
                .filter(pk=kwargs["pk"])
                .first()
            )
            if p is None:
                raise PermissionDenied
            if p.status != Payroll.Status.PENDING:
                messages.error(request, "Only pending payrolls can be approved.")
                return redirect("payroll:payroll_detail", pk=p.pk)
            p.status = Payroll.Status.APPROVED
            p.approved_by = request.user
            p.save(update_fields=["status", "approved_by"])
        messages.success(request, "Payroll approved.")
        return redirect("payroll:payroll_detail", pk=p.pk)


class PayrollPayView(PayrollAccessMixin, FormView):
    template_name = "payroll/payroll_pay.html"
    form_class = SalaryPaymentForm

    def dispatch(self, request, *args, **kwargs):
        self.payroll = get_object_or_404(Payroll, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["payroll"] = self.payroll
        return ctx

    def form_valid(self, form):
        with transaction.atomic():
            payroll = (
                Payroll.objects
                .select_for_update()
                .get(pk=self.payroll.pk)
            )
            if payroll.status != Payroll.Status.APPROVED:
                messages.error(
                    self.request, "Only approved payrolls can be paid."
                )
                return redirect("payroll:payroll_detail", pk=payroll.pk)

            payment = PayrollService.record_bank_payment(
                payroll,
                self.request.user,
                method=form.cleaned_data["method"],
                transaction_ref=form.cleaned_data["transaction_ref"],
            )
        messages.success(self.request, f"Payment of {payment.amount} recorded.")
        return redirect("payroll:payroll_detail", pk=payroll.pk)


class SalarySlipPDFView(PayrollAccessMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            from weasyprint import HTML
        except ImportError:
            messages.error(request, "PDF generation is unavailable.")
            return redirect("payroll:payroll_detail", pk=kwargs["pk"])

        payroll = get_object_or_404(Payroll, pk=kwargs["pk"])
        if payroll.status not in (Payroll.Status.APPROVED, Payroll.Status.PAID):
            messages.error(request, "Only approved or paid slips can be downloaded.")
            return redirect("payroll:payroll_detail", pk=payroll.pk)

        html = render_to_string(
            "payroll/salary_slip.html",
            {"payroll": payroll, "is_pdf": True},
            request=request,
        )
        pdf = HTML(
            string=html,
            base_url=request.build_absolute_uri("/"),
        ).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="salary-slip-{payroll.pk}.pdf"'
        )
        return response
