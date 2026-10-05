from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView, ListView, FormView

from apps.common.models import SchoolClass, Section, Subject, AcademicYear
from apps.students.models import Student
from .models import Attendance, AttendanceService
from .forms import AttendanceMarkFormSet, AttendanceFilterForm


class AttendanceMarkView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "attendance/mark.html"
    permission_required = "attendance.add_attendance"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["class_filter_form"] = AttendanceFilterForm(self.request.GET or None)
        ctx["formset"] = kwargs.get("formset")
        ctx["breadcrumbs"] = [{"title": "Mark Attendance"}]
        students_qs = None
        if "school_class" in self.request.GET and self.request.GET.get("school_class"):
            cls = get_object_or_404(SchoolClass, pk=self.request.GET.get("school_class"))
            sec_id = self.request.GET.get("section")
            date = self.request.GET.get("date")
            sub_id = self.request.GET.get("subject")
            ctx["selected_class"] = cls
            ctx["selected_date"] = date
            ctx["selected_subject_id"] = sub_id
            students_qs = Student.objects.filter(current_class=cls)
            if sec_id:
                students_qs = students_qs.filter(current_section_id=sec_id)
            initial = []
            for s in students_qs:
                initial.append({
                    "student_id": s.pk,
                    "student_name": s.full_name,
                    "status": "present",
                })
            ctx["formset"] = AttendanceMarkFormSet(initial=initial)
        return ctx

    def post(self, request, *args, **kwargs):
        formset = AttendanceMarkFormSet(request.POST)
        if not formset.is_valid():
            messages.error(request, "There were errors in the form.")
            return self.render_to_response(self.get_context_data(formset=formset))
        class_id = request.POST.get("school_class")
        section_id = request.POST.get("section")
        date_str = request.POST.get("date")
        subject_id = request.POST.get("subject")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            messages.error(request, "Invalid date.")
            return self.render_to_response(self.get_context_data(formset=formset))
        records = []
        for form in formset:
            if form.cleaned_data:
                records.append({
                    "student_id": form.cleaned_data["student_id"],
                    "status": form.cleaned_data["status"],
                    "notes": form.cleaned_data.get("notes", ""),
                })
        n = AttendanceService.mark_attendance(
            school_class_id=class_id, section_id=section_id,
            date=date_obj, subject_id=subject_id or None,
            records=records, user=request.user,
        )
        messages.success(request, f"Attendance marked for {n} student(s).")
        return redirect("attendance:daily_mark")


class AttendanceReportView(LoginRequiredMixin, ListView):
    template_name = "attendance/report.html"
    context_object_name = "records"
    paginate_by = 50

    def get_queryset(self):
        qs = Attendance.objects.select_related("student", "school_class", "academic_year")
        class_id = self.request.GET.get("class")
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        date = self.request.GET.get("date")
        if date:
            try:
                qs = qs.filter(date=datetime.strptime(date, "%Y-%m-%d").date())
            except Exception:
                pass
        student_q = self.request.GET.get("q")
        if student_q:
            qs = qs.filter(student__full_name__icontains=student_q) | qs.filter(student__registration_no__icontains=student_q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [{"title": "Attendance Report"}]
        return ctx
