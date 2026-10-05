"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.views import google_login_start, google_login_callback


def landing_page_view(request):
    """APS Lahore school website landing page (green & gold theme).
    Pulls real statistics + notices + events from the ERP backend."""
    from apps.common.models import AcademicYear, SchoolClass, Section, Subject
    from apps.students.models import Student
    from apps.teachers.models import Teacher
    from apps.announcements.models import Announcement
    from apps.school_calendar.models import CalendarEvent
    from django.utils import timezone
    today = timezone.now().date()
    return render(request, "landing.html", {
        "active_academic_year": AcademicYear.objects.get_active(),
        "total_students": Student.objects.filter(status=Student.Status.ACTIVE).count(),
        "total_teachers": Teacher.objects.filter(status=Teacher.Status.ACTIVE).count(),
        "total_classes": SchoolClass.objects.filter(is_active=True).count(),
        "total_sections": Section.objects.filter(is_active=True).count(),
        "total_subjects": Subject.objects.filter(is_active=True).count(),
        "latest_notices": Announcement.objects.filter(
            is_published=True
        ).select_related("author").order_by("-publish_date")[:3],
        "upcoming_events": CalendarEvent.objects.filter(
            start_date__gte=today
        ).order_by("start_date")[:4],
    })

# Import two_factor's core patterns directly — its urlconf module returns a
# tuple (patterns, app_namespace) which Django's include() doesn't handle
# correctly in 4.x. We assemble our own urlpatterns list instead.
from two_factor.urls import core as two_factor_core
from two_factor.urls import profile as two_factor_profile
from two_factor.urls import plugin_urlpatterns as two_factor_plugin


urlpatterns = [
    path("admin/", admin.site.urls),
    # Root URL → APS Lahore school website landing page (green & gold theme)
    path("", landing_page_view, name="landing"),
    # 2FA-enabled login + setup flow (django-two-factor-auth) — uses our custom MyAPS template
    *two_factor_core,
    *two_factor_profile,
    *two_factor_plugin,
    # Fallback plain logout
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Password change (when logged in)
    path("password-change/", auth_views.PasswordChangeView.as_view(
        template_name="registration/password_change.html"
    ), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html"
    ), name="password_change_done"),
    # Forgot password flow (Django built-in)
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html"
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        success_url="/reset/done/",
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html"
    ), name="password_reset_complete"),
    # Google OAuth login (set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env to enable)
    path("auth/google/start/", google_login_start, name="google_login_start"),
    path("auth/google/callback/", google_login_callback, name="google_login_callback"),
    # 2FA setup
    path("accounts/", include("apps.accounts.urls")),
    # Apps
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.common.urls")),
    path("students/", include("apps.students.urls")),
    path("parents/", include("apps.parents.urls")),
    path("teachers/", include("apps.teachers.urls")),
    path("admissions/", include("apps.admissions.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("diary/", include("apps.diary.urls")),
    path("homework/", include("apps.homework.urls")),
    path("syllabus/", include("apps.syllabus.urls")),
    path("examinations/", include("apps.examinations.urls")),
    path("datesheets/", include("apps.datesheets.urls")),
    path("fees/", include("apps.fees.urls")),
    path("payroll/", include("apps.payroll.urls")),
    path("activities/", include("apps.activities.urls")),
    path("announcements/", include("apps.announcements.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("calendar/", include("apps.school_calendar.urls")),
    path("reports/", include("apps.reports.urls")),
    path("audit-logs/", include("apps.audit_logs.urls")),
    path("portal/", include("apps.portal.urls")),
    # CSP report endpoint — receives violation reports from browsers
    path("csp-report/", csrf_exempt(lambda request: HttpResponse("OK", content_type="text/plain")),
         name="csp_report"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        path("static/<path:path>", serve, {"document_root": settings.STATIC_ROOT}),
    ]


# ---------------------------------------------------------------------------
# Custom error handlers — friendly pages, no raw tracebacks
# ---------------------------------------------------------------------------
def handler404_page(request, exception=None):
    return render(request, "404.html", status=404)

def handler500_page(request):
    return render(request, "500.html", status=500)

def handler403_page(request, exception=None):
    return render(request, "403.html", status=403)
