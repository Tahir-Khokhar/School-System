from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, View, TemplateView

from apps.students.models import Student
from .models import ClassTest, TestResult, SurpriseTest, Exam, ExamSubject, TermResult
from .forms import (
    ClassTestForm, SurpriseTestForm, ExamForm, ExamSubjectForm, TermResultForm,
    TestResultFormSet,
)


class ClassTestListView(LoginRequiredMixin, ListView):
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


class ClassTestDetailView(LoginRequiredMixin, DetailView):
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
        students = Student.objects.filter(current_class=self.test.school_class).order_by("full_name")
        ctx["students"] = students
        ctx["breadcrumbs"] = [
            {"title": "Class Tests", "url": reverse("examinations:classtest_list")},
            {"title": self.test.title, "url": reverse("examinations:classtest_detail", args=[self.test.pk])},
            {"title": "Results"},
        ]
        return ctx

    def post(self, request, *args, **kwargs):
        student_ids = request.POST.getlist("student_id")
        obtained = request.POST.getlist("obtained_marks")
        remarks = request.POST.getlist("remarks")
        for sid, marks, rem in zip(student_ids, obtained, remarks):
            TestResult.objects.update_or_create(
                test=self.test, student_id=sid,
                defaults={"obtained_marks": marks or 0, "remarks": rem or ""},
            )
        messages.success(request, "Marks saved.")
        return redirect("examinations:classtest_detail", pk=self.test.pk)


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


class ExamListView(LoginRequiredMixin, ListView):
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


class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = "examinations/exam_detail.html"
    context_object_name = "exam"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subjects"] = self.object.subjects.select_related("subject", "school_class")
        ctx["subject_form"] = ExamSubjectForm(initial={"exam": self.object})
        return ctx


class TermResultListView(LoginRequiredMixin, ListView):
    model = TermResult
    template_name = "examinations/termresult_list.html"
    context_object_name = "results"
    paginate_by = 25

    def get_queryset(self):
        qs = TermResult.objects.select_related("student", "academic_year")
        status = self.request.GET.get("status")
        if status:
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
        result.status = TermResult.Status.PUBLISHED
        result.save()
        messages.success(request, "Term result published.")
        return redirect("examinations:termresult_list")


class ReportCardPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from weasyprint import HTML
        result = get_object_or_404(TermResult, pk=kwargs["pk"])
        student = result.student
        html = render_to_string("examinations/report_card.html", {
            "result": result, "student": student, "is_pdf": True,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        return HttpResponse(pdf, content_type="application/pdf")
