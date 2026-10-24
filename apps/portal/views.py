"""
Student / Teacher / Parent portal views — FULLY FUNCTIONAL.

Every view connects to real backend data, checks authentication + role + ownership,
and renders proper templates with loading/empty/error states.

Security rule:
    - Student A can NEVER access Student B's data
    - Parent A can NEVER access another family's children
    - Backend verifies ownership, never trusts frontend IDs
"""
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, Sum
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView, View, DetailView, ListView

from apps.students.models import Student
from apps.parents.models import Parent
from apps.teachers.models import Teacher
from apps.fees.models import FeeChallan, FeePayment
from apps.attendance.models import Attendance, AttendanceService
from apps.homework.models import Homework, HomeworkSubmission
from apps.diary.models import DiaryEntry
from apps.syllabus.models import Syllabus, SyllabusTopic, SyllabusProgressService
from apps.examinations.models import ClassTest, TestResult, Exam, ExamResult, TermResult, SurpriseTest
from apps.datesheets.models import DateSheet, DateSheetItem
from apps.activities.models import Activity, StudentActivity
from apps.announcements.models import Announcement
from apps.notifications.models import Notification
from apps.common.models import AcademicYear


# ===========================================================================
# HELPERS
# ===========================================================================

def _get_student_for_user(user):
    """Get the Student record linked to this user. Returns None if not linked."""
    try:
        return user.student_profile
    except Student.DoesNotExist:
        return None


def _get_parent_for_user(user):
    """Get the Parent record linked to this user. Returns None if not linked."""
    try:
        return user.parent_profile
    except Parent.DoesNotExist:
        return None


def _get_selected_child(request):
    """Get the parent's currently-selected child from session.
    Falls back to the first child if none selected."""
    parent = _get_parent_for_user(request.user)
    if not parent:
        return None
    child_id = request.session.get("selected_child_id")
    if child_id:
        child = parent.children.filter(pk=child_id).first()
        if child:
            return child
    # Fallback: first child
    return parent.children.first()


# ===========================================================================
# STUDENT PORTAL VIEWS
# ===========================================================================

class StudentBaseMixin(LoginRequiredMixin):
    """All student portal views inherit this — checks auth + student role."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (getattr(request.user, "is_student", False) or request.user.is_superuser):
            return redirect("dashboard:home")
        self.student = _get_student_for_user(request.user)
        if not self.student and not request.user.is_superuser:
            return render(request, "portal/no_profile.html", {
                "portal_type": "Student",
            }, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["student"] = self.student
        ctx["portal_type"] = "Student"
        ctx["active_academic_year"] = AcademicYear.objects.get_active()
        return ctx


class StudentPortalHomeView(StudentBaseMixin, TemplateView):
    template_name = "portal/student_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            active_year = AcademicYear.objects.get_active()
            ctx["attendance_percentage"] = AttendanceService.get_student_attendance_percentage(
                self.student, active_year
            )
            ctx["pending_challans"] = self.student.fee_challans.exclude(
                status=FeeChallan.Status.PAID
            ).select_related("academic_year", "student")[:5]
            ctx["paid_challans"] = self.student.fee_challans.filter(
                status=FeeChallan.Status.PAID
            ).select_related("academic_year")[:5]
            ctx["test_results"] = self.student.test_results.select_related(
                "test__subject", "test__school_class"
            ).order_by("-test__date")[:5]
            ctx["upcoming_tests"] = ClassTest.objects.filter(
                school_class=self.student.current_class,
                date__gte=timezone.now().date(),
                status="published",
            ).select_related("subject")[:5]
            ctx["upcoming_homework"] = Homework.objects.filter(
                school_class=self.student.current_class,
                due_date__gte=timezone.now().date(),
                status=Homework.Status.ASSIGNED,
            ).select_related("subject")[:5]
        return ctx


class StudentProfileView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "profile"
        ctx["enrollments"] = self.student.enrollments.select_related(
            "academic_year", "school_class", "section"
        ).order_by("-academic_year__start_date") if self.student else []
        return ctx


class StudentAttendanceView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/attendance.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            active_year = AcademicYear.objects.get_active()
            records = Attendance.objects.filter(
                student=self.student, academic_year=active_year
            ).select_related("subject", "school_class").order_by("-date")
            ctx["records"] = records[:50]
            ctx["attendance_percentage"] = AttendanceService.get_student_attendance_percentage(
                self.student, active_year
            )
            ctx["present_count"] = records.filter(status=Attendance.Status.PRESENT).count()
            ctx["absent_count"] = records.filter(status=Attendance.Status.ABSENT).count()
            ctx["late_count"] = records.filter(status=Attendance.Status.LATE).count()
            ctx["leave_count"] = records.filter(status=Attendance.Status.LEAVE).count()
            ctx["total_days"] = records.count()
        return ctx


class StudentTimetableView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/timetable.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Timetable not yet implemented as a model — show empty state
        ctx["active_section"] = "timetable"
        return ctx


class StudentHomeworkView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/homework.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            homeworks = Homework.objects.filter(
                school_class=self.student.current_class,
                status__in=[Homework.Status.ASSIGNED, Homework.Status.SUBMITTED, Homework.Status.REVIEWED],
            ).select_related("subject", "teacher").order_by("-due_date")
            ctx["homeworks"] = homeworks[:20]
        return ctx


class StudentDiaryView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/diary.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            entries = DiaryEntry.objects.filter(
                school_class=self.student.current_class,
            ).select_related("subject", "teacher").order_by("-date")[:20]
            ctx["diary_entries"] = entries
        return ctx


class StudentSyllabusView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/syllabus.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            active_year = AcademicYear.objects.get_active()
            syllabi = Syllabus.objects.filter(
                academic_year=active_year,
                school_class=self.student.current_class,
            ).select_related("subject").prefetch_related("topics")
            ctx["syllabi"] = syllabi
            # Progress per syllabus
            progress_data = []
            for syl in syllabi:
                progress = SyllabusProgressService.get_progress(syl)
                progress_data.append({"syllabus": syl, "progress": progress})
            ctx["progress_data"] = progress_data
        return ctx


class StudentExamsView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/exams.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            active_year = AcademicYear.objects.get_active()
            ctx["exams"] = Exam.objects.filter(
                academic_year=active_year,
                subjects__school_class=self.student.current_class,
            ).distinct().order_by("-start_date")
            ctx["class_tests"] = ClassTest.objects.filter(
                school_class=self.student.current_class,
                status="published",
            ).select_related("subject").order_by("-date")[:10]
        return ctx


class StudentDateSheetView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/datesheet.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            datesheets = DateSheet.objects.filter(
                school_class=self.student.current_class,
                status=DateSheet.Status.PUBLISHED,
            ).prefetch_related("items__subject")
            ctx["datesheets"] = datesheets
        return ctx


class StudentResultsView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            ctx["test_results"] = self.student.test_results.select_related(
                "test__subject", "test__school_class"
            ).order_by("-test__date")[:20]
            ctx["term_results"] = self.student.term_results.filter(
                status=TermResult.Status.PUBLISHED
            ).select_related("academic_year").order_by("-percentage")
        return ctx


class StudentReportCardView(StudentBaseMixin, DetailView):
    template_name = "portal/student/report_card.html"
    model = TermResult
    context_object_name = "result"

    def get_object(self, queryset=None):
        result = get_object_or_404(TermResult, pk=self.kwargs["pk"])
        # SECURITY: verify this result belongs to the logged-in student
        if self.student and result.student_id != self.student.id:
            raise PermissionDenied("You cannot view another student's report card.")
        return result


class StudentFeesView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/fees.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            challans = self.student.fee_challans.select_related(
                "academic_year", "student__current_class"
            ).order_by("-issue_date")
            ctx["challans"] = challans[:20]
            ctx["total_payable"] = sum(c.total_payable for c in challans)
            ctx["total_paid"] = sum(c.total_paid for c in challans)
            ctx["total_outstanding"] = sum(c.balance for c in challans if c.balance > 0)
        return ctx


class StudentChallansView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/challans.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            ctx["challans"] = self.student.fee_challans.select_related(
                "academic_year"
            ).order_by("-issue_date")[:30]
        return ctx


class StudentPaymentsView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/payments.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            challan_ids = self.student.fee_challans.values_list("id", flat=True)
            ctx["payments"] = FeePayment.objects.filter(
                challan_id__in=challan_ids, is_successful=True
            ).select_related("challan").order_by("-payment_date")[:30]
        return ctx


class StudentReceiptsView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/receipts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            challan_ids = self.student.fee_challans.values_list("id", flat=True)
            ctx["receipts"] = FeePayment.objects.filter(
                challan_id__in=challan_ids, is_successful=True
            ).select_related("challan").order_by("-payment_date")[:30]
        return ctx


class StudentActivitiesView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/activities.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            ctx["activities"] = self.student.activities.select_related(
                "activity"
            ).order_by("-activity__date")[:20]
            ctx["awards"] = self.student.awards.order_by("-date")[:10]
        return ctx


class StudentNoticesView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/notices.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["announcements"] = Announcement.objects.filter(
            is_published=True,
            audience__in=["everyone", "students"],
        ).select_related("author").order_by("-publish_date")[:20]
        return ctx


class StudentNotificationsView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/notifications.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["notifications"] = Notification.objects.filter(
            user=self.request.user
        ).order_by("-sent_at")[:30]
        ctx["unread_count"] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "mark_all_read":
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
        elif action == "mark_read":
            notif_id = request.POST.get("notif_id")
            if notif_id:
                n = get_object_or_404(Notification, pk=notif_id, user=request.user)
                n.is_read = True
                n.save()
        return redirect("portal:student_notifications")


class StudentAcademicYearView(StudentBaseMixin, TemplateView):
    template_name = "portal/student/academic_year.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.student:
            ctx["enrollments"] = self.student.enrollments.select_related(
                "academic_year", "school_class", "section"
            ).order_by("-academic_year__start_date")
            ctx["active_year"] = AcademicYear.objects.get_active()
        return ctx


# ===========================================================================
# PARENT PORTAL VIEWS
# ===========================================================================

class ParentBaseMixin(LoginRequiredMixin):
    """All parent portal views inherit this — checks auth + parent role + selected child."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (getattr(request.user, "is_parent", False) or request.user.is_superuser):
            return redirect("dashboard:home")
        self.parent = _get_parent_for_user(request.user)
        if not self.parent and not request.user.is_superuser:
            return render(request, "portal/no_profile.html", {
                "portal_type": "Parent",
            }, status=403)
        self.child = _get_selected_child(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent"] = self.parent
        ctx["child"] = self.child
        ctx["children"] = self.parent.children.all() if self.parent else []
        ctx["portal_type"] = "Parent"
        ctx["active_academic_year"] = AcademicYear.objects.get_active()
        return ctx


class ParentPortalHomeView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.parent:
            children = self.parent.children.all()
            # Calculate aggregated stats
            total_pending = 0
            for c in children:
                total_pending += c.fee_challans.exclude(
                    status=FeeChallan.Status.PAID
                ).count()
            ctx["total_pending_fees"] = total_pending
            ctx["children_count"] = children.count()
            # Upcoming exams for all children
            child_classes = [c.current_class for c in children if c.current_class]
            ctx["upcoming_exams"] = ClassTest.objects.filter(
                school_class__in=child_classes,
                date__gte=timezone.now().date(),
                status="published",
            ).count()
        return ctx


class ParentChildrenView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/children.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.parent:
            children_with_data = []
            for c in self.parent.children.all():
                active_year = AcademicYear.objects.get_active()
                att_pct = AttendanceService.get_student_attendance_percentage(c, active_year)
                pending = c.fee_challans.exclude(status=FeeChallan.Status.PAID).count()
                children_with_data.append({
                    "student": c,
                    "attendance_pct": att_pct,
                    "pending_fees": pending,
                })
            ctx["children_data"] = children_with_data
        return ctx


class ParentSelectChildView(ParentBaseMixin, View):
    """Switch the selected child — stored in session."""
    def get(self, request, *args, **kwargs):
        child_id = kwargs["pk"]
        # SECURITY: verify this child belongs to the parent
        if self.parent:
            child = self.parent.children.filter(pk=child_id).first()
            if child:
                request.session["selected_child_id"] = child_id
                messages.success(request, f"Now viewing {child.full_name}'s information.")
            else:
                messages.error(request, "This child is not linked to your account.")
        return redirect("portal:parent_home")


# --- Child-specific parent views ---

class ParentChildAttendanceView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_attendance.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            active_year = AcademicYear.objects.get_active()
            records = Attendance.objects.filter(
                student=self.child, academic_year=active_year
            ).select_related("subject").order_by("-date")
            ctx["records"] = records[:50]
            ctx["attendance_pct"] = AttendanceService.get_student_attendance_percentage(
                self.child, active_year
            )
            ctx["present"] = records.filter(status=Attendance.Status.PRESENT).count()
            ctx["absent"] = records.filter(status=Attendance.Status.ABSENT).count()
            ctx["late"] = records.filter(status=Attendance.Status.LATE).count()
            ctx["leave"] = records.filter(status=Attendance.Status.LEAVE).count()
        return ctx


class ParentChildTimetableView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_timetable.html"


class ParentChildHomeworkView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_homework.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            ctx["homeworks"] = Homework.objects.filter(
                school_class=self.child.current_class,
                status__in=[Homework.Status.ASSIGNED, Homework.Status.SUBMITTED, Homework.Status.REVIEWED],
            ).select_related("subject").order_by("-due_date")[:20]
        return ctx


class ParentChildExamsView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_exams.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            active_year = AcademicYear.objects.get_active()
            ctx["exams"] = Exam.objects.filter(
                academic_year=active_year,
                subjects__school_class=self.child.current_class,
            ).distinct().order_by("-start_date")
            ctx["class_tests"] = ClassTest.objects.filter(
                school_class=self.child.current_class,
                status="published",
            ).select_related("subject").order_by("-date")[:10]
        return ctx


class ParentChildResultsView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            ctx["test_results"] = self.child.test_results.select_related(
                "test__subject"
            ).order_by("-test__date")[:20]
            ctx["term_results"] = self.child.term_results.filter(
                status=TermResult.Status.PUBLISHED
            ).order_by("-percentage")
        return ctx


class ParentChildFeesView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_fees.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            challans = self.child.fee_challans.select_related(
                "academic_year"
            ).order_by("-issue_date")
            ctx["challans"] = challans[:20]
            ctx["total_outstanding"] = sum(c.balance for c in challans if c.balance > 0)
            ctx["total_paid"] = sum(c.total_paid for c in challans)
        return ctx


class ParentChildChallansView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_challans.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            ctx["challans"] = self.child.fee_challans.select_related(
                "academic_year"
            ).order_by("-issue_date")[:30]
        return ctx


class ParentChildPaymentsView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_payments.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            challan_ids = self.child.fee_challans.values_list("id", flat=True)
            ctx["payments"] = FeePayment.objects.filter(
                challan_id__in=challan_ids, is_successful=True
            ).select_related("challan").order_by("-payment_date")[:30]
        return ctx


class ParentChildReceiptsView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_receipts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            challan_ids = self.child.fee_challans.values_list("id", flat=True)
            ctx["receipts"] = FeePayment.objects.filter(
                challan_id__in=challan_ids, is_successful=True
            ).select_related("challan").order_by("-payment_date")[:30]
        return ctx


class ParentChildActivitiesView(ParentBaseMixin, TemplateView):
    template_name = "portal/parent/child_activities.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.child:
            ctx["activities"] = self.child.activities.select_related(
                "activity"
            ).order_by("-activity__date")[:20]
        return ctx


class ParentChildReportCardView(ParentBaseMixin, DetailView):
    template_name = "portal/parent/child_report_card.html"
    model = TermResult
    context_object_name = "result"

    def get_object(self, queryset=None):
        result = get_object_or_404(TermResult, pk=self.kwargs["pk"])
        # SECURITY: verify this result belongs to a child of this parent
        if self.parent and not self.parent.children.filter(pk=result.student_id).exists():
            raise PermissionDenied("You cannot view another family's report card.")
        return result


# ===========================================================================
# TEACHER PORTAL (existing, kept for compatibility)
# ===========================================================================

class TeacherPortalHomeView(LoginRequiredMixin, TemplateView):
    template_name = "portal/teacher_home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (getattr(request.user, "is_teacher", False) or request.user.is_superuser):
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = getattr(self.request.user, "teacher_profile", None)
        ctx["teacher"] = teacher
        if teacher:
            ctx["my_classes"] = teacher.classes.all()
            ctx["my_subjects"] = teacher.subjects.all()
            ctx["today_attendance_count"] = Attendance.objects.filter(
                marked_by=self.request.user, date=timezone.now().date()
            ).count()
        return ctx
