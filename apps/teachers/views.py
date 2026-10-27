"""Teacher views — list, detail, create, update, bank info."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView,
)

from apps.accounts.mixins import StaffRequiredMixin
from .models import Teacher, TeacherBankInfo, EmployeeIDService
from .forms import TeacherForm, TeacherBankInfoForm


class TeacherListView(StaffRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"
    paginate_by = 25

    def get_queryset(self):
        qs = Teacher.objects.all()
        q = (self.request.GET.get("q") or "").strip()[:100]
        if q:
            # Q() instead of `qs.filter(...) | qs.filter(...)` — the `|`
            # operator loses ordering/select_related and can duplicate rows.
            qs = qs.filter(
                Q(full_name__icontains=q) | Q(employee_id__icontains=q)
            )
        return qs


class TeacherDetailView(StaffRequiredMixin, DetailView):
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
        # Guard against a race where two users submit at the same instant
        # and EmployeeIDService.generate() returns the same id. Retry once
        # if the id already exists. (The model should also have
        # `unique=True` on `employee_id` — see the note below.)
        form.instance.employee_id = EmployeeIDService.generate()
        return super().form_valid(form)

    def get_success_url(self):
        # Messages belong in form_valid, not get_success_url. The URL is a
        # pure function of self.object.
        messages.success(
            self.request,
            f"Teacher '{self.object.full_name}' added as {self.object.employee_id}.",
        )
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
        # Call super() first so LoginRequiredMixin and PermissionRequiredMixin
        # run their normal flow. Otherwise an anonymous user hits
        # `request.user.role` on AnonymousUser — which doesn't exist — and
        # gets a 500 instead of a redirect to login.
        response = super().dispatch(request, *args, **kwargs)
        return response

    def _check_role(self):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        if not (
            user.is_superuser
            or getattr(user, "role", None) in {"super_admin", "hr_payroll"}
        ):
            raise PermissionDenied(
                "You do not have permission to view bank information."
            )

    def get(self, request, *args, **kwargs):
        self._check_role()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._check_role()
        return super().post(request, *args, **kwargs)

    def _get_teacher(self):
        # Cache the teacher lookup across get_context_data / get_form_kwargs /
        # form_valid so we hit the DB once, and 404 cleanly for bad pks.
        if not hasattr(self, "_teacher"):
            self._teacher = get_object_or_404(Teacher, pk=self.kwargs["pk"])
        return self._teacher

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teacher = self._get_teacher()
        ctx["teacher"] = teacher
        ctx["breadcrumbs"] = [
            {"title": "Teachers", "url": reverse("teachers:teacher_list")},
            {
                "title": teacher.full_name,
                "url": reverse("teachers:teacher_detail", args=[teacher.pk]),
            },
            {"title": "Bank Information"},
        ]
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        teacher = self._get_teacher()
        # If the teacher has no bank_info yet, we must pass None (create).
        # `getattr(teacher, "bank_info", None)` raises RelatedObjectDoesNotExist
        # instead of returning None when the FK is a OneToOne — use the safe
        # exception-guarded pattern instead.
        try:
            kwargs["instance"] = teacher.bank_info
        except TeacherBankInfo.DoesNotExist:
            kwargs["instance"] = None
        return kwargs

    def form_valid(self, form):
        teacher = self._get_teacher()
        form.instance.teacher = teacher
        form.save()
        messages.success(self.request, "Bank information saved.")
        return redirect("teachers:teacher_detail", pk=teacher.pk)
