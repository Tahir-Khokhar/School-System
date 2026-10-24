from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    # ===== STUDENT PORTAL =====
    path("student/", views.StudentPortalHomeView.as_view(), name="student_home"),
    path("student/profile/", views.StudentProfileView.as_view(), name="student_profile"),
    path("student/attendance/", views.StudentAttendanceView.as_view(), name="student_attendance"),
    path("student/timetable/", views.StudentTimetableView.as_view(), name="student_timetable"),
    path("student/homework/", views.StudentHomeworkView.as_view(), name="student_homework"),
    path("student/diary/", views.StudentDiaryView.as_view(), name="student_diary"),
    path("student/syllabus/", views.StudentSyllabusView.as_view(), name="student_syllabus"),
    path("student/exams/", views.StudentExamsView.as_view(), name="student_exams"),
    path("student/datesheet/", views.StudentDateSheetView.as_view(), name="student_datesheet"),
    path("student/results/", views.StudentResultsView.as_view(), name="student_results"),
    path("student/report-card/<int:pk>/", views.StudentReportCardView.as_view(), name="student_report_card"),
    path("student/fees/", views.StudentFeesView.as_view(), name="student_fees"),
    path("student/challans/", views.StudentChallansView.as_view(), name="student_challans"),
    path("student/payments/", views.StudentPaymentsView.as_view(), name="student_payments"),
    path("student/receipts/", views.StudentReceiptsView.as_view(), name="student_receipts"),
    path("student/activities/", views.StudentActivitiesView.as_view(), name="student_activities"),
    path("student/notices/", views.StudentNoticesView.as_view(), name="student_notices"),
    path("student/notifications/", views.StudentNotificationsView.as_view(), name="student_notifications"),
    path("student/academic-year/", views.StudentAcademicYearView.as_view(), name="student_academic_year"),

    # ===== PARENT PORTAL =====
    path("parent/", views.ParentPortalHomeView.as_view(), name="parent_home"),
    path("parent/children/", views.ParentChildrenView.as_view(), name="parent_children"),
    path("parent/select-child/<int:pk>/", views.ParentSelectChildView.as_view(), name="parent_select_child"),
    # Child-specific views (all respect the selected child)
    path("parent/child/attendance/", views.ParentChildAttendanceView.as_view(), name="parent_attendance"),
    path("parent/child/timetable/", views.ParentChildTimetableView.as_view(), name="parent_timetable"),
    path("parent/child/homework/", views.ParentChildHomeworkView.as_view(), name="parent_homework"),
    path("parent/child/exams/", views.ParentChildExamsView.as_view(), name="parent_exams"),
    path("parent/child/results/", views.ParentChildResultsView.as_view(), name="parent_results"),
    path("parent/child/fees/", views.ParentChildFeesView.as_view(), name="parent_fees"),
    path("parent/child/challans/", views.ParentChildChallansView.as_view(), name="parent_challans"),
    path("parent/child/payments/", views.ParentChildPaymentsView.as_view(), name="parent_payments"),
    path("parent/child/receipts/", views.ParentChildReceiptsView.as_view(), name="parent_receipts"),
    path("parent/child/activities/", views.ParentChildActivitiesView.as_view(), name="parent_activities"),
    path("parent/child/report-card/<int:pk>/", views.ParentChildReportCardView.as_view(), name="parent_report_card"),

    # ===== TEACHER PORTAL =====
    path("teacher/", views.TeacherPortalHomeView.as_view(), name="teacher_home"),
]
