"""Common app views."""
from django.contrib import messages
from apps.accounts.mixins import StaffRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count
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


class AcademicYearDetailView(StaffRequiredMixin, DetailView):
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


class ClassListView(StaffRequiredMixin, ListView):
    """List of all school classes. Staff-only — students access their own
    class info via the portal (/portal/student/academic-year/), not via
    this admin page."""
    model = SchoolClass
    template_name = "common/class_list.html"
    context_object_name = "classes"
    paginate_by = 25

    def get_queryset(self):
        # prefetch_related sections + annotate student count to avoid
        # the N+1 from calling Section.student_count in the template.
        qs = (
            SchoolClass.objects
            .prefetch_related("sections")
            .annotate(total_students=Count("students", filter=Q(students__status="active")))
        )
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class ClassCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SchoolClass
    form_class = ClassForm
    template_name = "common/class_form.html"
    permission_required = "common.add_schoolclass"

    def get_success_url(self):
        from django.urls import reverse
        return reverse("common:class_list")


class SubjectListView(StaffRequiredMixin, ListView):
    """List of all subjects. Staff-only — students see their subjects via
    the portal syllabus view."""
    model = Subject
    template_name = "common/subject_list.html"
    context_object_name = "subjects"
    paginate_by = 25


class SubjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "common/subject_form.html"
    permission_required = "common.add_subject"

    def get_success_url(self):
        from django.urls import reverse
        return reverse("common:subject_list")


class GlobalSearchView(LoginRequiredMixin, TemplateView):
    """Permission-aware global search. Returns ONLY the records the logged-in
    user is allowed to see based on their role + Django permissions.

    PII guard:
      - Students see only their own records (no other students, no parents,
        no challans except their own).
      - Parents see only their linked children's records.
      - Staff with the appropriate view_* permission see the full result set.
      - Anyone without the right permission gets an empty result set for that
        model — never an unfiltered leak.
    """
    template_name = "common/search_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        ctx["q"] = q
        if not q:
            return ctx

        from apps.students.models import Student
        from apps.teachers.models import Teacher
        from apps.parents.models import Parent
        from apps.fees.models import FeeChallan
        from apps.examinations.models import ClassTest

        user = self.request.user
        is_staff = bool(user.is_superuser or user.role in {
            "super_admin", "admin", "principal", "coordinator",
            "accountant", "hr_payroll", "receptionist",
        })

        # ---- Students ----
        # Only staff with view_student OR the student seeing their own record.
        if is_staff and user.has_perm("students.view_student"):
            ctx["students"] = Student.objects.filter(
                Q(full_name__icontains=q) | Q(registration_no__icontains=q)
            ).values_list("pk", "registration_no", "full_name", named=True)[:8]
        elif user.role == "student":
            student = getattr(user, "student_profile", None)
            if student and (
                q.lower() in student.full_name.lower()
                or q.lower() in student.registration_no.lower()
            ):
                ctx["students"] = [student]  # only self — never other students
            else:
                ctx["students"] = []
        else:
            ctx["students"] = []

        # ---- Teachers ----
        # Only staff with view_teacher.
        if is_staff and user.has_perm("teachers.view_teacher"):
            ctx["teachers"] = Teacher.objects.filter(
                Q(full_name__icontains=q) | Q(employee_id__icontains=q)
            ).values_list("pk", "employee_id", "full_name", named=True)[:8]
        else:
            ctx["teachers"] = []

        # ---- Parents ----
        # Only staff with view_parent (receptionist/admin). Parents/students
        # never see other families' CNICs/phones.
        if is_staff and user.has_perm("parents.view_parent"):
            ctx["parents"] = Parent.objects.filter(
                Q(full_name__icontains=q) | Q(cnic__icontains=q)
            ).values_list("pk", "full_name", "cnic", named=True)[:8]
        else:
            ctx["parents"] = []

        # ---- Fee challans ----
        # Staff with view_feechallan see all; students/parents see only their own.
        if is_staff and user.has_perm("fees.view_feechallan"):
            ctx["challans"] = FeeChallan.objects.filter(challan_no__icontains=q)[:8]
        elif user.role == "student":
            student = getattr(user, "student_profile", None)
            ctx["challans"] = (
                student.fee_challans.filter(challan_no__icontains=q)[:8]
                if student else []
            )
        elif user.role == "parent":
            parent = getattr(user, "parent_profile", None)
            if parent:
                child_ids = parent.children.values_list("pk", flat=True)
                ctx["challans"] = FeeChallan.objects.filter(
                    challan_no__icontains=q, student_id__in=child_ids
                )[:8]
            else:
                ctx["challans"] = []
        else:
            ctx["challans"] = []

        # ---- Class tests ----
        # Staff with view_classtest OR students seeing tests for their own class.
        if is_staff and user.has_perm("examinations.view_classtest"):
            ctx["tests"] = ClassTest.objects.filter(title__icontains=q)[:8]
        elif user.role == "student":
            student = getattr(user, "student_profile", None)
            ctx["tests"] = (
                ClassTest.objects.filter(
                    title__icontains=q,
                    school_class=student.current_class,
                )[:8] if student else []
            )
        else:
            ctx["tests"] = []

        return ctx
