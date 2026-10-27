"""
Report Center — high-level report index pages.
Individual PDFs (challan, receipt, salary slip, report card) live in their
respective apps.
"""
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, F
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView, ListView, View

from apps.accounts.mixins import StaffRequiredMixin
from apps.students.models import Student
from apps.fees.models import FeeChallan
from apps.attendance.models import Attendance
from apps.payroll.models import Payroll
from apps.teachers.models import Teacher


class ReportIndexView(StaffRequiredMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Report Center"}]
        return ctx


class StudentReportView(StaffRequiredMixin, ListView):
    model = Student
    template_name = "reports/student_report.html"
    context_object_name = "students"
    paginate_by = 50

    def get_queryset(self):
        # select_related so the report template doesn't fire an N+1 when
        # rendering current_class; order_by so pagination is deterministic.
        return (
            Student.objects
            .select_related("current_class", "current_section")
            .order_by("full_name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Report Center", "url": reverse("reports:index")},
            {"title": "Students"},
        ]
        return ctx


class FeeReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FeeChallan
    template_name = "reports/fee_report.html"
    context_object_name = "challans"
    paginate_by = 50
    permission_required = "fees.view_feechallan"

    def get_queryset(self):
        return (
            FeeChallan.objects
            .select_related("student", "academic_year")
            .order_by("-issue_date")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # DB-side aggregate over the FULL queryset, not just the page and
        # not a Python loop that iterates every row.
        agg = FeeChallan.objects.aggregate(
            collected=Sum("total_paid"),
            outstanding=Sum(F("total_payable") - F("amount_paid")),
        )
        ctx["total_collected"] = agg["collected"] or Decimal("0")
        ctx["total_outstanding"] = agg["outstanding"] or Decimal("0")
        return ctx


class AttendanceReportView(StaffRequiredMixin, ListView):
    model = Attendance
    template_name = "reports/attendance_report.html"
    context_object_name = "records"
    paginate_by = 50

    def get_queryset(self):
        # select_related so the template doesn't N+1, order_by for stable
        # pagination.
        return (
            Attendance.objects
            .select_related("student", "school_class", "academic_year")
            .order_by("-date", "student__full_name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Report Center", "url": reverse("reports:index")},
            {"title": "Attendance"},
        ]
        return ctx


class PayrollReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Payroll
    template_name = "reports/payroll_report.html"
    context_object_name = "payrolls"
    paginate_by = 50
    permission_required = "payroll.view_payroll"

    def get_queryset(self):
        return (
            Payroll.objects
            .select_related("teacher")
            .order_by("-month")
        )


class DefaulterReportPDFView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "fees.view_feechallan"

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML

        challans_qs = (
            FeeChallan.objects
            .filter(
                status__in=[
                    FeeChallan.Status.UNPAID,
                    FeeChallan.Status.PARTIAL,
                    FeeChallan.Status.OVERDUE,
                ]
            )
            .select_related("student", "academic_year", "student__current_class")
            .order_by("due_date")
        )

        # DB-side aggregate — do not pull every challan into Python just
        # to sum.
        agg = challans_qs.aggregate(
            outstanding=Sum(F("total_payable") - F("amount_paid"))
        )
        total_outstanding = agg["outstanding"] or Decimal("0")

        html = render_to_string("reports/defaulter_pdf.html", {
            "challans": challans_qs,
            "total_outstanding": total_outstanding,
            "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="defaulter_report.pdf"'
        return response
