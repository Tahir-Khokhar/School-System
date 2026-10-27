"""Student views — list, detail, create, update, archive."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, View,
)

from apps.accounts.mixins import StaffRequiredMixin
from .models import Student, StudentEnrollment, RegistrationNumberService
from .forms import StudentForm


class StudentListView(StaffRequiredMixin, ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 25

    def get_queryset(self):
        qs = Student.objects.select_related("current_class")
        q = (self.request.GET.get("q") or "").strip()[:100]
        if q:
            # Q() instead of `qs.filter(...) | qs.filter(...)` — `|` drops
            # select_related and can duplicate/UNION rows.
            qs = qs.filter(
                Q(full_name__icontains=q) | Q(registration_no__icontains=q)
            )
        class_id = self.request.GET.get("class")
        if class_id:
            # Validate the pk — a garbage value would raise ValueError on
            # the filter and 500 the list view.
            try:
                qs = qs.filter(current_class_id=int(class_id))
            except (TypeError, ValueError):
                pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Students"}]
        from apps.common.models import SchoolClass
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        return ctx


class StudentDetailView(StaffRequiredMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_queryset(self):
        # select_related current_class so the template's class name lookup
        # doesn't fire an N+1 query.
        return Student.objects.select_related("current_class")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Students", "url": reverse("students:student_list")},
            {"title": str(self.object)},
        ]
        ctx["enrollments"] = self.object.enrollments.select_related(
            "academic_year", "school_class"
        )
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
        # RegistrationNumberService.generate() must be collision-safe.
        # If Student.registration_no is unique=True, an IntegrityError here
        # becomes a 500 under concurrency. Retry a few times.
        from django.db import IntegrityError, transaction

        last_error = None
        for _ in range(5):
            form.instance.registration_no = RegistrationNumberService.generate()
            try:
                with transaction.atomic():
                    response = super().form_valid(form)
                messages.success(
                    self.request,
                    f"Student '{self.object.full_name}' registered as "
                    f"{self.object.registration_no}.",
                )
                return response
            except IntegrityError as exc:
                last_error = exc
                # Reset the in-memory instance's pk so a retry doesn't
                # reuse a half-saved object.
                form.instance.pk = None
                continue

        messages.error(
            self.request,
            "Could not allocate a registration number; please try again.",
        )
        return self.form_invalid(form)

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
            {
                "title": str(self.object),
                "url": reverse("students:student_detail", args=[self.object.pk]),
            },
            {"title": "Edit"},
        ]
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Student updated.")
        return reverse("students:student_detail", args=[self.object.pk])


class StudentArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "students.change_student"

    def post(self, request, *args, **kwargs):
        # get_object_or_404 instead of Student.objects.get — the latter
        # 500s on a bad pk, which is a DOS-ish 500 for a trivial typo'd URL.
        student = get_object_or_404(Student, pk=kwargs["pk"])
        student.status = Student.Status.INACTIVE
        # update_fields so we don't re-save every column (and don't bump
        # updated_at unless you actually want to).
        student.save(update_fields=["status", "updated_at"])
        messages.success(request, f"{student.full_name} archived.")
        return redirect("students:student_list")
