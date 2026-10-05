from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView

from .models import CalendarEvent
from .forms import CalendarEventForm


class CalendarEventListView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = "school_calendar/event_list.html"
    context_object_name = "events"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "School Calendar"}]
        return ctx


class CalendarEventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = "school_calendar/event_form.html"
    permission_required = "school_calendar.add_calendarevent"

    def get_success_url(self):
        messages.success(self.request, "Calendar event created.")
        return reverse("school_calendar:event_list")
