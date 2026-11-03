
"""Premium admin dashboard — daily operations control center."""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import redirect
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
    """
    Role-aware dashboard.

    Superusers and authorized admin staff access the staff dashboard.
    Students, parents, and teachers are redirected to their respective portals.
    Unauthorized authenticated users receive HTTP 403.
    """

    template_name = "dashboard/home.html"
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        # Let LoginRequiredMixin handle anonymous users.
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        user = request.user

        # Superusers must be checked before their assigned role.
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Redirect users to their respective portals.
        portal_redirects = {
            "student": "portal:student_home",
            "parent": "portal:parent_home",
            "teacher": "portal:teacher_home",
        }

        portal_url = portal_redirects.get(user.role)

        if portal_url:
            return redirect(portal_url)

        # Only authorized staff can access the admin dashboard.
        if not user.is_admin_staff:
            raise PermissionDenied(
                "You do not have permission to access the admin dashboard."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get the currently authenticated user.
        user = self.request.user

        # Use the configured Django timezone for the current school date.
        today = timezone.localdate()

        active_year = AcademicYear.objects.get_active()

        # --------------------------------------------------
        # GENERAL DASHBOARD STATISTICS
        # --------------------------------------------------

        ctx["total_students"] = Student.objects.filter(
            status=Student.Status.ACTIVE
        ).count()

        ctx["total_teachers"] = Teacher.objects.filter(
            status=Teacher.Status.ACTIVE
        ).count()

        ctx["total_classes"] = SchoolClass.objects.filter(
            is_active=True
        ).count()

        ctx["active_academic_year"] = active_year

        # --------------------------------------------------
        # ATTENDANCE STATISTICS
        # --------------------------------------------------

        ctx["students_present_today"] = Attendance.objects.filter(
            date=today,
            status=Attendance.Status.PRESENT,
        ).count()

        ctx["students_absent_today"] = Attendance.objects.filter(
            date=today,
            status=Attendance.Status.ABSENT,
        ).count()

        # --------------------------------------------------
        # ACADEMIC STATISTICS
        # --------------------------------------------------

        ctx["tests_today"] = ClassTest.objects.filter(
            date=today
        ).count()

        ctx["homework_today"] = Homework.objects.filter(
            assigned_date=today
        ).count()

        ctx["pending_results"] = TermResult.objects.exclude(
            status=TermResult.Status.PUBLISHED
        ).count()

        ctx["upcoming_homework"] = Homework.objects.filter(
            due_date__gte=today,
            status=Homework.Status.ASSIGNED,
        ).count()

        # --------------------------------------------------
        # FINANCIAL PERMISSIONS
        # --------------------------------------------------

        can_view_finance = (
            user.is_superuser
            or user.has_perm("fees.view_feepayment")
        )

        ctx["can_view_finance"] = can_view_finance

        if can_view_finance:

            ctx["fee_payments_today"] = FeePayment.objects.filter(
                payment_date=today,
                is_successful=True,
            ).count()

            ctx["fee_defaulters"] = FeeChallan.objects.filter(
                status__in=[
                    FeeChallan.Status.UNPAID,
                    FeeChallan.Status.OVERDUE,
                    FeeChallan.Status.PARTIAL,
                ]
            ).count()

            ctx["recent_payments"] = FeePayment.objects.select_related(
                "challan",
                "challan__student",
            ).order_by("-payment_date")[:5]

            # --------------------------------------------------
            # MONTHLY FEE COLLECTION CHART
            # --------------------------------------------------

            collection_data = defaultdict(Decimal)

            six_months_ago = today - timedelta(days=180)

            payments = FeePayment.objects.filter(
                is_successful=True,
                payment_date__gte=six_months_ago,
                payment_date__lte=today,
            ).order_by("payment_date").values(
                "payment_date",
                "amount",
            )

            for payment in payments:
                month_label = payment["payment_date"].strftime("%b %y")
                amount = payment["amount"] or Decimal("0")

                collection_data[month_label] += amount

            # Pass Python lists directly for json_script.
            ctx["collection_labels"] = list(
                collection_data.keys()
            )

            ctx["collection_values"] = [
                float(value)
                for value in collection_data.values()
            ]

        else:

            # Do not expose financial information to unauthorized staff.
            ctx["fee_payments_today"] = 0
            ctx["fee_defaulters"] = 0
            ctx["recent_payments"] = FeePayment.objects.none()

            ctx["collection_labels"] = []
            ctx["collection_values"] = []

        # --------------------------------------------------
        # STUDENT ENROLLMENT CHART
        # --------------------------------------------------

        enrollment_data = [
            {
                "name": school_class.name,
                "count": school_class.student_count,
            }
            for school_class in SchoolClass.objects.filter(
                is_active=True
            ).annotate(
                student_count=Count(
                    "students",
                    filter=Q(
                        students__status=Student.Status.ACTIVE
                    ),
                )
            ).order_by("order")
        ]

        # Keep this as a Python list, not json.dumps().
        ctx["enrollment_data"] = enrollment_data

        # --------------------------------------------------
        # RECENT SCHOOL ACTIVITIES
        # --------------------------------------------------

        ctx["recent_activities"] = Activity.objects.select_related(
            "academic_year"
        ).order_by("-date")[:5]

        # --------------------------------------------------
        # RECENT ANNOUNCEMENTS
        # --------------------------------------------------

        ctx["recent_announcements"] = Announcement.objects.filter(
            is_published=True
        ).select_related(
            "author"
        ).order_by("-publish_date")[:5]

        # --------------------------------------------------
        # UPCOMING EXAMINATIONS
        # --------------------------------------------------

        if active_year:
            ctx["upcoming_exams"] = ClassTest.objects.filter(
                date__gte=today
            ).select_related(
                "school_class",
                "subject",
            ).order_by("date")[:5]

        else:
            ctx["upcoming_exams"] = ClassTest.objects.none()

        return ctx
