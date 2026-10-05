from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from .models import Syllabus, SyllabusTopic, LecturePlan, SyllabusProgressService
from .forms import SyllabusForm, SyllabusTopicForm, LecturePlanForm


class SyllabusListView(LoginRequiredMixin, ListView):
    model = Syllabus
    template_name = "syllabus/syllabus_list.html"
    context_object_name = "syllabi"
    paginate_by = 25

    def get_queryset(self):
        qs = Syllabus.objects.select_related("school_class", "subject", "academic_year")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Syllabus"}]
        return ctx


class SyllabusDetailView(LoginRequiredMixin, DetailView):
    model = Syllabus
    template_name = "syllabus/syllabus_detail.html"
    context_object_name = "syllabus"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["progress"] = SyllabusProgressService.get_progress(self.object)
        ctx["topics"] = self.object.topics.all().order_by("priority")
        return ctx


class SyllabusCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Syllabus
    form_class = SyllabusForm
    template_name = "syllabus/syllabus_form.html"
    permission_required = "syllabus.add_syllabus"

    def get_success_url(self):
        messages.success(self.request, "Syllabus created.")
        return reverse("syllabus:syllabus_detail", args=[self.object.pk])


class SyllabusTopicCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SyllabusTopic
    form_class = SyllabusTopicForm
    template_name = "syllabus/topic_form.html"
    permission_required = "syllabus.add_syllabustopic"

    def dispatch(self, request, *args, **kwargs):
        self.syllabus = Syllabus.objects.get(pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["syllabus"] = self.syllabus
        return ctx

    def form_valid(self, form):
        form.instance.syllabus = self.syllabus
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Topic added.")
        return reverse("syllabus:syllabus_detail", args=[self.syllabus.pk])


class SyllabusTopicUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SyllabusTopic
    form_class = SyllabusTopicForm
    template_name = "syllabus/topic_form.html"
    permission_required = "syllabus.change_syllabustopic"

    def get_success_url(self):
        messages.success(self.request, "Topic updated.")
        return reverse("syllabus:syllabus_detail", args=[self.object.syllabus_id])


class LecturePlanListView(LoginRequiredMixin, ListView):
    model = LecturePlan
    template_name = "syllabus/lecture_list.html"
    context_object_name = "lectures"
    paginate_by = 25


class LecturePlanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LecturePlan
    form_class = LecturePlanForm
    template_name = "syllabus/lecture_form.html"
    permission_required = "syllabus.add_lectureplan"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Lecture plan saved.")
        return reverse("syllabus:lecture_list")
