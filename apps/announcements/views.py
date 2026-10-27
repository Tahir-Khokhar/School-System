from django.contrib import messages
from apps.accounts.mixins import StaffRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from apps.notifications.models import NotificationService
from .models import Announcement
from .forms import AnnouncementForm


class AnnouncementListView(LoginRequiredMixin, ListView):
    """Announcement list — filtered by audience so students/parents/teachers
    only see announcements targeted at them.

    Audience rules:
      - EVERYONE: visible to all logged-in users.
      - TEACHERS: visible to teachers + admin staff (admin staff see everything).
      - STUDENTS: visible to students + admin staff.
      - PARENTS: visible to parents + admin staff.
      - ADMIN: visible ONLY to admin staff (and superuser).
      - CLASS / SECTION: visible to students enrolled in that class/section +
        their parents + admin staff.
    """
    model = Announcement
    template_name = "announcements/list.html"
    context_object_name = "announcements"
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.filter(is_published=True).select_related(
            "author", "target_class", "target_section",
        )

        # Admin staff see everything (no audience filter).
        is_admin = bool(
            user.is_superuser
            or user.role in {"super_admin", "admin", "principal", "coordinator",
                             "accountant", "hr_payroll", "receptionist"}
        )
        if is_admin:
            return qs

        # Build an OR filter for the audiences this user belongs to.
        from django.db.models import Q
        user_audiences = [Announcement.Audience.EVERYONE]
        if user.role == "teacher":
            user_audiences.append(Announcement.Audience.TEACHERS)
        elif user.role == "student":
            user_audiences.append(Announcement.Audience.STUDENTS)
        elif user.role == "parent":
            user_audiences.append(Announcement.Audience.PARENTS)

        base_filter = Q(audience__in=user_audiences)

        # Class/Section targeted announcements: include if the user is a student
        # in that class/section, or a parent of such a student.
        if user.role == "student":
            student = getattr(user, "student_profile", None)
            if student:
                # Student sees announcements targeted at their class/section.
                base_filter |= Q(
                    audience=Announcement.Audience.CLASS,
                    target_class=student.current_class,
                )
                if student.current_section:
                    base_filter |= Q(
                        audience=Announcement.Audience.SECTION,
                        target_section=student.current_section,
                    )
        elif user.role == "parent":
            parent = getattr(user, "parent_profile", None)
            if parent:
                # Parent sees announcements targeted at their children's classes/sections.
                child_classes = [c.current_class for c in parent.children.all() if c.current_class]
                child_sections = [c.current_section for c in parent.children.all() if c.current_section]
                if child_classes:
                    base_filter |= Q(
                        audience=Announcement.Audience.CLASS,
                        target_class__in=child_classes,
                    )
                if child_sections:
                    base_filter |= Q(
                        audience=Announcement.Audience.SECTION,
                        target_section__in=child_sections,
                    )

        return qs.filter(base_filter).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Announcements"}]
        return ctx


class AnnouncementDetailView(StaffRequiredMixin, DetailView):
    model = Announcement
    template_name = "announcements/detail.html"
    context_object_name = "announcement"


class AnnouncementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcements/form.html"
    permission_required = "announcements.add_announcement"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Notify the relevant audience.
        # Bug fix: previously the audience_map didn't include CLASS/SECTION,
        # so those fell into the `else` branch and notified ALL users (PII leak).
        # Now CLASS/SECTION notifications are scoped to students in that class
        # (and their parents), and the bulk-notify path is ONLY used for
        # audience=EVERYONE.
        from apps.accounts.models import User
        from apps.students.models import Student
        audience = self.object.audience
        title = self.object.title
        message = self.object.description[:200]

        role_audience_map = {
            Announcement.Audience.TEACHERS: User.Role.TEACHER,
            Announcement.Audience.STUDENTS: User.Role.STUDENT,
            Announcement.Audience.PARENTS: User.Role.PARENT,
            Announcement.Audience.ADMIN: User.Role.ADMIN,
        }
        if audience == Announcement.Audience.EVERYONE:
            # Bulk notify every active user — only this branch hits the loop.
            NotificationService.notify_user_queryset(
                User.objects.filter(is_active=True),
                title, message, "announcement",
            )
        elif audience in role_audience_map:
            # Notify just that role.
            NotificationService.notify_role(
                role_audience_map[audience], title, message, "announcement",
            )
        elif audience == Announcement.Audience.CLASS:
            # Notify students in the target_class + their parents.
            students = Student.objects.filter(
                current_class=self.object.target_class,
                status=Student.Status.ACTIVE,
            ).select_related("user", "parent", "parent__user")
            for s in students:
                if s.user:
                    NotificationService.notify(s.user, title, message, "announcement")
                if s.parent and s.parent.user:
                    NotificationService.notify(s.parent.user, title, message, "announcement")
        elif audience == Announcement.Audience.SECTION:
            # Notify students in target_section + their parents.
            students = Student.objects.filter(
                current_section=self.object.target_section,
                status=Student.Status.ACTIVE,
            ).select_related("user", "parent", "parent__user")
            for s in students:
                if s.user:
                    NotificationService.notify(s.user, title, message, "announcement")
                if s.parent and s.parent.user:
                    NotificationService.notify(s.parent.user, title, message, "announcement")
        messages.success(self.request, "Announcement published.")
        return response

    def get_success_url(self):
        return reverse("announcements:detail", args=[self.object.pk])
