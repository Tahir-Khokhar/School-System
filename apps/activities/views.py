from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from .models import Activity
from .forms import ActivityForm


class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = "activities/activity_list.html"
    context_object_name = "activities"
    paginate_by = 25

    def get_queryset(self):
        qs = Activity.objects.all()
        cat = self.request.GET.get("category")
        if cat:
            qs = qs.filter(category=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category_choices"] = Activity.Category.choices
        ctx["breadcrumbs"] = [{"title": "Activities"}]
        return ctx


class ActivityDetailView(LoginRequiredMixin, DetailView):
    model = Activity
    template_name = "activities/activity_detail.html"
    context_object_name = "activity"


class ActivityCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = "activities/activity_form.html"
    permission_required = "activities.add_activity"

    def get_success_url(self):
        messages.success(self.request, "Activity created.")
        return reverse("activities:activity_list")
