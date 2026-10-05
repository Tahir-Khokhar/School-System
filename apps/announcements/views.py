from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from apps.notifications.models import NotificationService
from .models import Announcement
from .forms import AnnouncementForm


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/list.html"
    context_object_name = "announcements"
    paginate_by = 25

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True).select_related("author")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Announcements"}]
        return ctx


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
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
        # Notify the relevant audience
        from apps.accounts.models import User
        audience_map = {
            Announcement.Audience.EVERYONE: None,  # notify all
            Announcement.Audience.TEACHERS: User.Role.TEACHER,
            Announcement.Audience.STUDENTS: User.Role.STUDENT,
            Announcement.Audience.PARENTS: User.Role.PARENT,
            Announcement.Audience.ADMIN: User.Role.ADMIN,
        }
        role = audience_map.get(self.object.audience)
        if role:
            NotificationService.notify_role(role, self.object.title, self.object.description[:200], "announcement", "")
        else:
            for u in User.objects.filter(is_active=True):
                NotificationService.notify(u, self.object.title, self.object.description[:200], "announcement", "")
        messages.success(self.request, "Announcement published.")
        return response

    def get_success_url(self):
        return reverse("announcements:detail", args=[self.object.pk])
