"""Common app views."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView, CreateView, DetailView, TemplateView, View,
)

from .models import AcademicYear, SchoolClass, Subject
from .forms import AcademicYearForm, ClassForm, SubjectForm


class AcademicYearListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AcademicYear
    template_name = "common/academic_year_list.html"
    context_object_name = "years"
    permission_required = "common.view_academicyear"
    paginate_by = 25


class AcademicYearCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = "common/academic_year_form.html"
    permission_required = "common.add_academicyear"
    extra_context = {"breadcrumbs": [{"title": "Academic Years", "url": "/academic-years/"}, {"title": "New"}]}

    def get_success_url(self):
        messages.success(self.request, f"Academic Year '{self.object.name}' created.")
        return "/academic-years/"


class AcademicYearDetailView(LoginRequiredMixin, DetailView):
    model = AcademicYear
    template_name = "common/academic_year_detail.html"
    context_object_name = "year"


class AcademicYearActivateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "common.change_academicyear"

    def post(self, request, *args, **kwargs):
        year = get_object_or_404(AcademicYear, pk=kwargs["pk"])
        AcademicYear.objects.filter(is_active=True).update(is_active=False)
        year.is_active = True
        year.save()
        messages.success(request, f"{year.name} is now the active academic year.")
        return redirect("common:academic_year_list")


class ClassListView(LoginRequiredMixin, ListView):
    model = SchoolClass
    template_name = "common/class_list.html"
    context_object_name = "classes"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("sections")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class ClassCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SchoolClass
    form_class = ClassForm
    template_name = "common/class_form.html"
    permission_required = "common.add_schoolclass"
    success_url = "/classes/"


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "common/subject_list.html"
    context_object_name = "subjects"
    paginate_by = 25


class SubjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "common/subject_form.html"
    permission_required = "common.add_subject"
    success_url = "/subjects/"


class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = "common/search_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        ctx["q"] = q
        if not q:
            return ctx
        # Lazy imports to avoid circulars
        from apps.students.models import Student
        from apps.teachers.models import Teacher
        from apps.parents.models import Parent
        from apps.fees.models import FeeChallan
        from apps.examinations.models import ClassTest

        ctx["students"] = Student.objects.filter(
            Q(full_name__icontains=q) | Q(registration_no__icontains=q)
        )[:8]
        ctx["teachers"] = Teacher.objects.filter(
            Q(full_name__icontains=q) | Q(employee_id__icontains=q)
        )[:8]
        ctx["parents"] = Parent.objects.filter(
            Q(full_name__icontains=q) | Q(cnic__icontains=q)
        )[:8]
        ctx["challans"] = FeeChallan.objects.filter(challan_no__icontains=q)[:8]
        ctx["tests"] = ClassTest.objects.filter(title__icontains=q)[:8]
        return ctx
