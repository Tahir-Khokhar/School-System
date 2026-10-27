"""Examination views — class tests, surprise tests, term exams, results, PDFs."""
import math

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import (
    ListView, CreateView, DetailView, View, TemplateView,
)

from apps.accounts.mixins import StaffRequiredMixin
from apps.students.models import Student
from .models import (
    ClassTest, TestResult, SurpriseTest, Exam, ExamSubject, TermResult,
)
from .forms import (
    ClassTestForm, SurpriseTestForm, ExamForm, ExamSubjectForm, TermResultForm,
    TestResultFormSet,
)


# ---------------------------------------------------------------------------
# Class Tests
# ---------------------------------------------------------------------------
class ClassTestListView(StaffRequiredMixin, ListView):
    model = ClassTest
    template_name = "examinations/classtest_list.html"
    context_object_name = "tests"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Class Tests"}]
        return ctx


class ClassTestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClassTest
    form_class = ClassTestForm
    template_name = "examinations/classtest_form.html"
    permission_required = "examinations.add_classtest"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Class test created.")
        return reverse("examinations:classtest_detail", args=[self.object.pk])


class ClassTestDetailView(StaffRequiredMixin, DetailView):
    model = ClassTest
    template_name = "examinations/classtest_detail.html"
    context_object_name = "test"


class ClassTestResultsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "examinations/classtest_results.html"
    permission_required = "examinations.add_testresult"

    def dispatch(self, request, *args, **kwargs):
        self.test = get_object_or_404(ClassTest, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["test"] = self.test
        students = Student.objects.filter(
            current_class=self.test.school_class
        ).order_by("full_name")
        ctx["students"] = students
        ctx["breadcrumbs"] = [
            {"title": "Class Tests", "url": reverse("examinations:classtest_list")},
            {
                "title": self.test.title,
                "url": reverse(
                    "examinations:classtest_detail", args=[self.test.pk]
                ),
            },
            {"title": "Results"},
        ]
        return ctx

    def post(self, request, *args, **kwargs):
        # ---------------------------------------------------------------
        # FIX #1 — restrict to students actually in this test's class.
        # Without this, a staff member (or attacker with add_testresult)
        # can post arbitrary student IDs and write results for a student
        # in a different class / school. 
        # ---------------------------------------------------------------
        allowed_student_ids = set(
            Student.objects
            .filter(current_class=self.test.school_class)
            .values_list("pk", flat=True)
        )

        student_ids = request.POST.getlist("student_id")
        obtained = request.POST.getlist("obtained_marks")
        remarks = request.POST.getlist("remarks")

        # FIX #2 — zip() silently truncates to the shortest list, so a
        # malformed POST with more marks than IDs would silently drop
        # input. Compare lengths up front.
        if not (len(student_ids) == len(obtained) == len(remarks)):
            messages.error(request, "Form data was corrupted; please retry.")
            return redirect(
                "examinations:classtest_detail", pk=self.test.pk
            )

        errors = []
        to_update = []
        to_create = []

        # FIX #3 — validate everything first, then write in a single
        # transaction. The old version could partially save (some students
        # updated, others skipped on error) leaving inconsistent data.
        for sid, marks, rem in zip(student_ids, obtained, remarks):
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                errors.append(f"Invalid student id {sid!r}")
                continue

            if sid_int not in allowed_student_ids:
                errors.append(
                    f"Student #{sid_int} is not in this class"
                )
                continue

            try:
                marks_val = float(marks) if marks else 0
            except (TypeError, ValueError):
                errors.append(f"Invalid marks {marks!r} for student #{sid_int}")
                continue

            # FIX #4 — reject nan/inf *before* float comparison
            if not math.isfinite(marks_val):
                errors.append(
                    f"Invalid marks {marks!r} for student #{sid_int}"
                )
                continue

            if marks_val < 0:
                errors.append(
                    f"Marks cannot be negative for student #{sid_int}"
                )
                continue

            if marks_val > float(self.test.total_marks):
                errors.append(
                    f"Marks ({marks_val}) exceed total marks "
                    f"({self.test.total_marks}) for student #{sid_int}"
                )
                continue

            to_update.append((sid_int, marks_val, (rem or "")))

        if errors:
            messages.error(
                request, "Some marks were not saved: " + "; ".join(errors)
            )
            # Do not write anything if any row failed — all-or-nothing.
            return redirect(
                "examinations:classtest_detail", pk=self.test.pk
            )

        # All valid — write in one transaction so a mid-loop crash doesn't
        # leave half the class updated.
        try:
            with transaction.atomic():
                for sid_int, marks_val, rem in to_update:
                    TestResult.objects.update_or_create(
                        test=self.test,
                        student_id=sid_int,
                        defaults={
                            "obtained_marks": marks_val,
                            "remarks": rem,
                        },
                    )
        except Exception:
            # Log and report; don't show the raw exception to staff.
            import logging
            logging.getLogger(__name__).exception(
                "Failed to save class-test results for test %s", self.test.pk
            )
            messages.error(request, "Could not save results; please try again.")
            return redirect(
                "examinations:classtest_detail", pk=self.test.pk
            )

        messages.success(request, "Marks saved successfully.")
        return redirect(
            "examinations:classtest_detail", pk=self.test.pk
        )


# ---------------------------------------------------------------------------
# Surprise Tests
# ---------------------------------------------------------------------------
class SurpriseTestListView(LoginRequiredMixin, ListView):
    model = SurpriseTest
    template_name = "examinations/surprisetest_list.html"
    context_object_name = "tests"
    paginate_by = 25


class SurpriseTestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SurpriseTest
    form_class = SurpriseTestForm
    template_name = "examinations/surprisetest_form.html"
    permission_required = "examinations.add_surprisetest"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Surprise test created.")
        return reverse("examinations:surprisetest_list")


# ---------------------------------------------------------------------------
# Term Exams
# ---------------------------------------------------------------------------
class ExamListView(StaffRequiredMixin, ListView):
    model = Exam
    template_name = "examinations/exam_list.html"
    context_object_name = "exams"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Term Exams"}]
        return ctx


class ExamCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = "examinations/exam_form.html"
    permission_required = "examinations.add_exam"

    def get_success_url(self):
        messages.success(self.request, "Term exam created.")
        return reverse("examinations:exam_list")


class ExamDetailView(StaffRequiredMixin, DetailView):
    model = Exam
    template_name = "examinations/exam_detail.html"
    context_object_name = "exam"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subjects"] = self.object.subjects.select_related(
            "subject", "school_class"
        )
        ctx["subject_form"] = ExamSubjectForm(initial={"exam": self.object})
        return ctx


# ---------------------------------------------------------------------------
# Term Results
# ---------------------------------------------------------------------------
class TermResultListView(StaffRequiredMixin, ListView):
    model = TermResult
    template_name = "examinations/termresult_list.html"
    context_object_name = "results"
    paginate_by = 25

    def get_queryset(self):
        qs = TermResult.objects.select_related("student", "academic_year")
        status = self.request.GET.get("status")
        if status and status in TermResult.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = TermResult.Status.choices
        ctx["breadcrumbs"] = [{"title": "Term Results"}]
        return ctx


class TermResultPublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "examinations.change_termresult"

    def post(self, request, *args, **kwargs):
        result = get_object_or_404(TermResult, pk=kwargs["pk"])
        # Only flip the status field; don't rewrite every column.
        if result.status != TermResult.Status.PUBLISHED:
            result.status = TermResult.Status.PUBLISHED
            result.save(update_fields=["status"])
            messages.success(request, "Term result published.")
        else:
            messages.info(request, "Term result is already published.")
        return redirect("examinations:termresult_list")


class ReportCardPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from weasyprint import HTML

        result = get_object_or_404(
            TermResult.objects.select_related("student", "academic_year"),
            pk=kwargs["pk"],
        )

        # FIX #5 — students/parents should only see their own report card.
        # Staff can see any. Without this, any logged-in user can guess a
        # TermResult pk and download another student's marks.
        is_staff = (
            request.user.is_staff
            or getattr(request.user, "is_admin_staff", False)
            or request.user.has_perm("examinations.view_termresult")
        )
        is_owner = getattr(result.student, "user_id", None) == request.user.pk
        if not (is_staff or is_owner):
            return HttpResponseNotFound("Report card not found.")

        student = result.student
        html = render_to_string(
            "examinations/report_card.html",
            {"result": result, "student": student, "is_pdf": True},
            request=request,
        )
        pdf = HTML(
            string=html, base_url=request.build_absolute_uri("/")
        ).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="report_card_{student.registration_no}.pdf"'
        )
        return response
