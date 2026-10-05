from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from .models import Homework
from .forms import HomeworkForm


class HomeworkListView(LoginRequiredMixin, ListView):
    model = Homework
    template_name = "homework/homework_list.html"
    context_object_name = "homeworks"
    paginate_by = 25

    def get_queryset(self):
        qs = Homework.objects.select_related("school_class", "subject")
        class_id = self.request.GET.get("class")
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.common.models import SchoolClass
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [{"title": "Homework"}]
        return ctx


class HomeworkCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Homework
    form_class = HomeworkForm
    template_name = "homework/homework_form.html"
    permission_required = "homework.add_homework"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Homework created.")
        return reverse("homework:homework_list")


class HomeworkDetailView(LoginRequiredMixin, DetailView):
    model = Homework
    template_name = "homework/homework_detail.html"
    context_object_name = "homework"


class HomeworkUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Homework
    form_class = HomeworkForm
    template_name = "homework/homework_form.html"
    permission_required = "homework.change_homework"

    def get_success_url(self):
        messages.success(self.request, "Homework updated.")
        return reverse("homework:homework_detail", args=[self.object.pk])
