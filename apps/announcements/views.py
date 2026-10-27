"""Announcement views — list, detail, create."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from apps.accounts.mixins import StaffRequiredMixin
from apps.notifications.models import NotificationService
from .models import Announcement
from .forms import AnnouncementForm


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/list.html"
    context_object_name = "announcements"
    paginate_by = 25

    def get_queryset(self):
        # FIX #1 — order explicitly. Without ordering, paginated results
        # are nondeterministic on Postgres (announcements can appear on two
        # pages, or vanish between page loads).
        return (
            Announcement.objects
            .filter(is_published=True)
            .select_related("author")
            .order_by("-published_at", "-created_at")
        )

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

        # FIX #2 — save the announcement inside a transaction with the
        # notification fan-out. If notification fails, the announcement
        # still exists but the user gets a warning instead of a silent
        # half-state.
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Failed to create announcement"
            )
            messages.error(
                self.request, "Could not save announcement; please retry."
            )
            return self.form_invalid(form)

        # FIX #3 — notify OUTSIDE the transaction so a slow/broken
        # notification backend doesn't hold the DB lock, and so failures
        # don't roll back the announcement itself.
        try:
            self._notify_audience()
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Announcement %s saved but notification fan-out failed",
                self.object.pk,
            )
            messages.warning(
                self.request,
                "Announcement saved, but some recipients could not be notified.",
            )
        else:
            messages.success(self.request, "Announcement published.")

        return response

    def _notify_audience(self):
        from apps.accounts.models import User

        audience = self.object.audience
        title = self.object.title
        body = self.object.description[:200]

        # FIX #4 — Audience.EVERYONE should fan out via the "everyone"
        # recipient set, not by iterating every active user one-by-one.
        # The old code called NotificationService.notify() in a loop, which
        # is O(users) separate inserts and can hammer the DB for a school
        # with 2000+ users.
        if audience == Announcement.Audience.EVERYONE:
            NotificationService.notify_all(
                title, body, "announcement", "",
            )
            return

        role_map = {
            Announcement.Audience.TEACHERS: User.Role.TEACHER,
            Announcement.Audience.STUDENTS: User.Role.STUDENT,
            Announcement.Audience.PARENTS: User.Role.PARENT,
            Announcement.Audience.ADMIN: User.Role.ADMIN,
        }
        role = role_map.get(audience)
        if role is None:
            # Unknown audience — do not silently notify everyone, which
            # would leak announcements to the wrong group.
            import logging
            logging.getLogger(__name__).warning(
                "Unknown audience %r on announcement %s",
                audience, self.object.pk,
            )
            return

        NotificationService.notify_role(role, title, body, "announcement", "")

    def get_success_url(self):
        return reverse("announcements:detail", args=[self.object.pk])
