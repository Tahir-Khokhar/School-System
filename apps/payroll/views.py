from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, View, FormView
from django.views.generic.detail import SingleObjectMixin

from apps.teachers.models import Teacher
from .models import Payroll, SalaryPayment, PayrollService
from .forms import PayrollForm, SalaryPaymentForm


class PayrollAccessMixin:
    """Only HR/Payroll role or superuser can view payroll."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.role in {"super_admin", "hr_payroll"}):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PayrollListView(LoginRequiredMixin, PayrollAccessMixin, ListView):
    model = Payroll
    template_name = "payroll/payroll_list.html"
    context_object_name = "payrolls"
    paginate_by = 25

    def get_queryset(self):
        qs = Payroll.objects.select_related("teacher")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(teacher__full_name__icontains=q) | qs.filter(teacher__employee_id__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Payroll.Status.choices
        ctx["breadcrumbs"] = [{"title": "Teacher Payroll"}]
        return ctx


class PayrollCreateView(LoginRequiredMixin, PayrollAccessMixin, CreateView):
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
            t = Teacher.objects.get(pk=teacher_id)
            initial["teacher"] = t
            initial["basic_salary"] = t.basic_salary
        return initial

    def get_success_url(self):
        messages.success(self.request, "Payroll record created.")
        return reverse("payroll:payroll_detail", args=[self.object.pk])


class PayrollDetailView(LoginRequiredMixin, PayrollAccessMixin, DetailView):
    model = Payroll
    template_name = "payroll/payroll_detail.html"
    context_object_name = "payroll"


class PayrollApproveView(LoginRequiredMixin, PayrollAccessMixin, SingleObjectMixin, View):
    model = Payroll

    def post(self, request, *args, **kwargs):
        p = self.get_object()
        p.status = Payroll.Status.APPROVED
        p.approved_by = request.user
        p.save(update_fields=["status", "approved_by"])
        messages.success(request, "Payroll approved.")
        return redirect("payroll:payroll_detail", pk=p.pk)


class PayrollPayView(LoginRequiredMixin, PayrollAccessMixin, FormView):
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
        payment = PayrollService.record_bank_payment(
            self.payroll, self.request.user,
            method=form.cleaned_data["method"],
            transaction_ref=form.cleaned_data["transaction_ref"],
        )
        messages.success(self.request, f"Payment of {payment.amount} recorded.")
        return redirect("payroll:payroll_detail", pk=self.payroll.pk)


class SalarySlipPDFView(LoginRequiredMixin, PayrollAccessMixin, View):
    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        payroll = get_object_or_404(Payroll, pk=kwargs["pk"])
        html = render_to_string("payroll/salary_slip.html", {
            "payroll": payroll, "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        return HttpResponse(pdf, content_type="application/pdf")
