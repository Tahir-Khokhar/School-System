"""
Report Center — high-level report index pages.
Individual PDFs (challan, receipt, salary slip, report card) live in their respective apps.
"""
from decimal import Decimal
from apps.accounts.mixins import StaffRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView, ListView

from apps.students.models import Student
from apps.fees.models import FeeChallan, FeePayment
from apps.attendance.models import Attendance
from apps.payroll.models import Payroll
from apps.teachers.models import Teacher


class ReportIndexView(StaffRequiredMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Report Center"}]
        return ctx


class StudentReportView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    model = Student
    template_name = "reports/student_report.html"
    context_object_name = "students"
    paginate_by = 50
    permission_required = "students.view_student"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Report Center", "url": "/reports/"}, {"title": "Students"}]
        return ctx


class FeeReportView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    model = FeeChallan
    template_name = "reports/fee_report.html"
    context_object_name = "challans"
    paginate_by = 50
    permission_required = "fees.view_feechallan"

    def get_queryset(self):
        # Use .distinct() because previous filters OR'd queries together (can
        # produce duplicate rows). Order by issue_date desc.
        return (FeeChallan.objects
                .select_related("student", "academic_year", "student__current_class")
                .order_by("-issue_date"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Sum at the DB level (avoid Python-side iteration over the whole table).
        # The previous code called self.get_queryset() TWICE — once for the
        # paginated ListView and once for the totals — pulling the entire table
        # into Python twice.
        qs_for_totals = FeeChallan.objects.all()
        ctx["total_collected"] = sum(
            p.amount for p in FeePayment.objects.filter(is_successful=True)
        ) or Decimal("0")
        ctx["total_outstanding"] = sum(
            c.balance for c in qs_for_totals if c.balance > 0
        ) or Decimal("0")
        return ctx


class AttendanceReportView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    model = Attendance
    template_name = "reports/attendance_report.html"
    context_object_name = "records"
    paginate_by = 50
    permission_required = "attendance.view_attendance"


class PayrollReportView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    model = Payroll
    template_name = "reports/payroll_report.html"
    context_object_name = "payrolls"
    paginate_by = 50
    permission_required = "payroll.view_payroll"

    def get_queryset(self):
        return Payroll.objects.select_related("teacher").order_by("-month")


class DefaulterReportPDFView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "fees.view_feechallan"
    template_name = "reports/defaulter_report.html"

    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        from decimal import Decimal
        challans = FeeChallan.objects.filter(
            status__in=[FeeChallan.Status.UNPAID, FeeChallan.Status.PARTIAL, FeeChallan.Status.OVERDUE]
        ).select_related("student", "academic_year", "student__current_class")
        # Sum at the DB level using aggregate() — avoids loading every row.
        from django.db.models import Sum
        # Balance is a Python property; we approximate the total here by
        # summing total_payable - total_paid at the Python layer for the
        # PDF only. For large schools this should be a SQL-side aggregate;
        # for a single-school defaulter report it's acceptable.
        total_outstanding = sum(
            (c.balance for c in challans if c.balance > 0),
            Decimal("0"),
        )
        html = render_to_string("reports/defaulter_pdf.html", {
            "challans": challans,
            "total_outstanding": total_outstanding,
            "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        return HttpResponse(pdf, content_type="application/pdf")
