"""Premium admin dashboard — daily operations control center."""
from collections import Counter, defaultdict
from datetime import timedelta
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Q
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.fees.models import FeeChallan, FeePayment
from apps.attendance.models import Attendance
from apps.homework.models import Homework
from apps.examinations.models import ClassTest, TermResult
from apps.activities.models import Activity
from apps.announcements.models import Announcement
from apps.common.models import AcademicYear, SchoolClass


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Role-aware dashboard.

    Unauthenticated users are redirected to the login page by
    LoginRequiredMixin. Authenticated users are routed by role:
    superusers and admin staff see the full staff dashboard; students,
    parents and teachers are redirected to their own portal; any other
    authenticated role gets a 403 (clearer than bouncing to a login
    page they are already past).
    """
    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        # Superusers (e.g. created via createsuperuser, which now sets
        # role=SUPER_ADMIN) and admin staff see the full dashboard.
        if user.is_superuser or user.is_admin_staff:
            return super().dispatch(request, *args, **kwargs)
        # Portal roles → their own home.
        if user.role == user.Role.STUDENT:
            return redirect("portal:student_home")
        if user.role == user.Role.PARENT:
            return redirect("portal:parent_home")
        if user.role == user.Role.TEACHER:
            return redirect("portal:teacher_home")
        # Authenticated but unrecognised role → 403, not a login redirect.
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        active_year = AcademicYear.objects.get_active()

        ctx["total_students"] = Student.objects.filter(status=Student.Status.ACTIVE).count()
        ctx["total_teachers"] = Teacher.objects.filter(status=Teacher.Status.ACTIVE).count()
        ctx["total_classes"] = SchoolClass.objects.filter(is_active=True).count()
        ctx["active_academic_year"] = active_year

        ctx["students_present_today"] = Attendance.objects.filter(
            date=today, status=Attendance.Status.PRESENT
        ).count()
        ctx["students_absent_today"] = Attendance.objects.filter(
            date=today, status=Attendance.Status.ABSENT
        ).count()
        ctx["tests_today"] = ClassTest.objects.filter(date=today).count()
        ctx["homework_today"] = Homework.objects.filter(assigned_date=today).count()

        # Financial KPIs — only shown to roles with finance visibility.
        # We use the Django permission system instead of hardcoded role
        # names so the check matches whatever create_school_roles assigns.
        user = self.request.user
        ctx["can_view_finance"] = user.is_superuser or user.has_perm("fees.view_feepayment")
        if ctx["can_view_finance"]:
            ctx["fee_payments_today"] = FeePayment.objects.filter(
                payment_date=today, is_successful=True
            ).count()
            ctx["fee_defaulters"] = FeeChallan.objects.filter(
                status__in=[FeeChallan.Status.UNPAID, FeeChallan.Status.OVERDUE, FeeChallan.Status.PARTIAL]
            ).count()
            ctx["recent_payments"] = FeePayment.objects.select_related(
                "challan", "challan__student"
            ).order_by("-payment_date")[:5]
            # Chart data — pass Python lists directly; the template serializes
            # them with the json_script tag (single encode, XSS-safe).
            collection_data = defaultdict(float)
            six_months_ago = today - timedelta(days=180)
            for p in FeePayment.objects.filter(
                is_successful=True, payment_date__gte=six_months_ago
            ).values("payment_date", "amount"):
                key = p["payment_date"].strftime("%b %y")
                collection_data[key] += float(p["amount"])
            ctx["collection_labels"] = list(collection_data.keys())
            ctx["collection_values"] = list(collection_data.values())
        else:
            ctx["fee_payments_today"] = 0
            ctx["fee_defaulters"] = 0
            ctx["recent_payments"] = FeePayment.objects.none()
            ctx["collection_labels"] = []
            ctx["collection_values"] = []

        ctx["pending_results"] = TermResult.objects.exclude(
            status=TermResult.Status.PUBLISHED
        ).count()
        ctx["upcoming_homework"] = Homework.objects.filter(
            due_date__gte=today, status__in=[Homework.Status.ASSIGNED]
        ).count()

        # Enrollment chart data — list of {name, count} dicts; the template
        # serializes with json_script.
        ctx["enrollment_data"] = [
            {"name": c.name, "count": c.student_count}
            for c in SchoolClass.objects.filter(is_active=True).annotate(
                student_count=Count("students", filter=Q(students__status=Student.Status.ACTIVE))
            ).order_by("order")
        ]

        ctx["recent_activities"] = Activity.objects.select_related(
            "academic_year"
        ).order_by("-date")[:5]

        ctx["recent_announcements"] = Announcement.objects.filter(
            is_published=True
        ).select_related("author").order_by("-publish_date")[:5]

        if active_year:
            ctx["upcoming_exams"] = ClassTest.objects.filter(
                date__gte=today
            ).select_related("school_class", "subject").order_by("date")[:5]
        else:
            ctx["upcoming_exams"] = ClassTest.objects.none()

        return ctx
