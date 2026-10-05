from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView

from .models import Teacher, TeacherBankInfo, EmployeeIDService
from .forms import TeacherForm, TeacherBankInfoForm


class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"
    paginate_by = 25

    def get_queryset(self):
        qs = Teacher.objects.all()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(employee_id__icontains=q)
        return qs


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"
    context_object_name = "teacher"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Teachers", "url": reverse("teachers:teacher_list")},
            {"title": str(self.object)},
        ]
        return ctx


class TeacherCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    permission_required = "teachers.add_teacher"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Teachers", "url": reverse("teachers:teacher_list")},
            {"title": "New Teacher"},
        ]
        return ctx

    def form_valid(self, form):
        form.instance.employee_id = EmployeeIDService.generate()
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, f"Teacher '{self.object.full_name}' added as {self.object.employee_id}.")
        return reverse("teachers:teacher_detail", args=[self.object.pk])


class TeacherUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    permission_required = "teachers.change_teacher"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Teachers", "url": reverse("teachers:teacher_list")},
            {"title": str(self.object)},
            {"title": "Edit"},
        ]
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Teacher updated.")
        return reverse("teachers:teacher_detail", args=[self.object.pk])


class TeacherBankInfoView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Sensitive: only HR/Payroll or super admin."""
    template_name = "teachers/teacher_bank_info.html"
    form_class = TeacherBankInfoForm
    permission_required = "payroll.view_payroll"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if not (user.is_superuser or getattr(user, "role", None) in {"super_admin", "hr_payroll"}):
            raise PermissionDenied("You do not have permission to view bank information.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import Teacher
        ctx["teacher"] = Teacher.objects.get(pk=self.kwargs["pk"])
        ctx["breadcrumbs"] = [
            {"title": "Teachers", "url": reverse("teachers:teacher_list")},
            {"title": ctx["teacher"].full_name, "url": reverse("teachers:teacher_detail", args=[ctx["teacher"].pk])},
            {"title": "Bank Information"},
        ]
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        teacher = Teacher.objects.get(pk=self.kwargs["pk"])
        instance = getattr(teacher, "bank_info", None)
        kwargs["instance"] = instance
        return kwargs

    def form_valid(self, form):
        teacher = Teacher.objects.get(pk=self.kwargs["pk"])
        form.instance.teacher = teacher
        form.save()
        messages.success(self.request, "Bank information saved.")
        return redirect("teachers:teacher_detail", pk=teacher.pk)
