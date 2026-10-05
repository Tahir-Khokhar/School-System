from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from .models import Student, StudentEnrollment
from .forms import StudentForm


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 25

    def get_queryset(self):
        qs = Student.objects.all()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(registration_no__icontains=q)
        class_id = self.request.GET.get("class")
        if class_id:
            qs = qs.filter(current_class_id=class_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Students"}]
        from apps.common.models import SchoolClass
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        return ctx


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Students", "url": reverse("students:student_list")},
            {"title": str(self.object)},
        ]
        ctx["enrollments"] = self.object.enrollments.select_related("academic_year", "school_class")
        return ctx


class StudentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    permission_required = "students.add_student"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Students", "url": reverse("students:student_list")},
            {"title": "New Student"},
        ]
        return ctx

    def form_valid(self, form):
        from .models import RegistrationNumberService
        form.instance.registration_no = RegistrationNumberService.generate()
        response = super().form_valid(form)
        messages.success(self.request, f"Student '{self.object.full_name}' registered as {self.object.registration_no}.")
        return response

    def get_success_url(self):
        return reverse("students:student_detail", args=[self.object.pk])


class StudentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    permission_required = "students.change_student"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Students", "url": reverse("students:student_list")},
            {"title": str(self.object), "url": reverse("students:student_detail", args=[self.object.pk])},
            {"title": "Edit"},
        ]
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Student updated.")
        return reverse("students:student_detail", args=[self.object.pk])


class StudentArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "students.change_student"

    def post(self, request, *args, **kwargs):
        from .models import Student
        student = Student.objects.get(pk=kwargs["pk"])
        student.status = Student.Status.INACTIVE
        student.save()
        messages.success(request, f"{student.full_name} archived.")
        return redirect("students:student_list")
