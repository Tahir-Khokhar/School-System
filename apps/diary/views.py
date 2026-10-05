from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from .models import DiaryEntry
from .forms import DiaryEntryForm


class DiaryEntryListView(LoginRequiredMixin, ListView):
    model = DiaryEntry
    template_name = "diary/entry_list.html"
    context_object_name = "entries"
    paginate_by = 25

    def get_queryset(self):
        qs = DiaryEntry.objects.select_related("school_class", "section", "subject", "teacher")
        class_id = self.request.GET.get("class")
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(topic__icontains=q) | qs.filter(lecture_summary__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.common.models import SchoolClass
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [{"title": "Daily Diary"}]
        return ctx


class DiaryEntryDetailView(LoginRequiredMixin, DetailView):
    model = DiaryEntry
    template_name = "diary/entry_detail.html"
    context_object_name = "entry"


class DiaryEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/entry_form.html"
    permission_required = "diary.add_diaryentry"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Diary entry added.")
        return reverse("diary:entry_list")


class DiaryEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/entry_form.html"
    permission_required = "diary.change_diaryentry"

    def get_success_url(self):
        messages.success(self.request, "Diary entry updated.")
        return reverse("diary:entry_detail", args=[self.object.pk])
