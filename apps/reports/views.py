"""
Report Center — high-level report index pages.
Individual PDFs (challan, receipt, salary slip, report card) live in their respective apps.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView, ListView

from apps.students.models import Student
from apps.fees.models import FeeChallan
from apps.attendance.models import Attendance
from apps.payroll.models import Payroll
from apps.teachers.models import Teacher


class ReportIndexView(LoginRequiredMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Report Center"}]
        return ctx


class StudentReportView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "reports/student_report.html"
    context_object_name = "students"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Report Center", "url": "/reports/"}, {"title": "Students"}]
        return ctx


class FeeReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FeeChallan
    template_name = "reports/fee_report.html"
    context_object_name = "challans"
    paginate_by = 50
    permission_required = "fees.view_feechallan"

    def get_queryset(self):
        return FeeChallan.objects.select_related("student", "academic_year").order_by("-issue_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_collected"] = sum(c.total_paid for c in self.get_queryset())
        ctx["total_outstanding"] = sum(c.balance for c in self.get_queryset())
        return ctx


class AttendanceReportView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = "reports/attendance_report.html"
    context_object_name = "records"
    paginate_by = 50


class PayrollReportView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Payroll
    template_name = "reports/payroll_report.html"
    context_object_name = "payrolls"
    paginate_by = 50
    permission_required = "payroll.view_payroll"

    def get_queryset(self):
        return Payroll.objects.select_related("teacher").order_by("-month")


class DefaulterReportPDFView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "fees.view_feechallan"
    template_name = "reports/defaulter_report.html"

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        challans = FeeChallan.objects.filter(
            status__in=[FeeChallan.Status.UNPAID, FeeChallan.Status.PARTIAL, FeeChallan.Status.OVERDUE]
        ).select_related("student", "academic_year", "student__current_class")
        html = render_to_string("reports/defaulter_pdf.html", {
            "challans": challans,
            "total_outstanding": sum(c.balance for c in challans),
            "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        return HttpResponse(pdf, content_type="application/pdf")
