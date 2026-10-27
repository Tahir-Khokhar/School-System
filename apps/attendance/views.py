"""Attendance views — daily marking and reports."""
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, ListView, FormView

from apps.accounts.mixins import StaffRequiredMixin
from apps.common.models import SchoolClass, Section, Subject, AcademicYear
from apps.students.models import Student
from .models import Attendance, AttendanceService
from .forms import AttendanceMarkFormSet, AttendanceFilterForm


def _parse_date(raw):
    """Return a date or None — never raise on user input."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _safe_int(raw):
    """Return int or None — never raise on user input."""
    if raw in (None, "", "None"):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


class AttendanceMarkView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "attendance/mark.html"
    permission_required = "attendance.add_attendance"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["class_filter_form"] = AttendanceFilterForm(self.request.GET or None)
        ctx["formset"] = kwargs.get("formset")  # may be None on first GET
        ctx["breadcrumbs"] = [{"title": "Mark Attendance"}]

        class_id = _safe_int(self.request.GET.get("school_class"))
        if not class_id:
            return ctx

        cls = get_object_or_404(SchoolClass, pk=class_id)

        # FIX #1 — validate the section belongs to this class. Otherwise a
        # user can pass ?school_class=1&section=999 and the initial formset
        # ends up empty (or worse, with wrong students once
        # `current_section_id` matches another class's section).
        section_id = _safe_int(self.request.GET.get("section"))
        if section_id is not None:
            if not Section.objects.filter(pk=section_id, school_class=cls).exists():
                section_id = None

        date = _parse_date(self.request.GET.get("date"))
        subject_id = _safe_int(self.request.GET.get("subject"))

        ctx["selected_class"] = cls
        ctx["selected_date"] = date.isoformat() if date else ""
        ctx["selected_subject_id"] = subject_id or ""

        students_qs = Student.objects.filter(current_class=cls)
        if section_id is not None:
            students_qs = students_qs.filter(current_section_id=section_id)

        # FIX #2 — attach the formset to the view instance so `post()` can
        # reuse it if needed, and pass initial only when we're NOT re-rendering
        # a failed POST (kwargs["formset"] would already be set).
        if "formset" not in kwargs:
            initial = [
                {
                    "student_id": s.pk,
                    "student_name": s.full_name,
                    "status": "present",
                }
                for s in students_qs
            ]
            ctx["formset"] = AttendanceMarkFormSet(initial=initial)
        return ctx

    def post(self, request, *args, **kwargs):
        formset = AttendanceMarkFormSet(request.POST)

        # FIX #3 — parse and validate filters BEFORE the formset, so the
        # context on a failed render still has the right class/date/subject.
        class_id = _safe_int(request.POST.get("school_class"))
        section_id = _safe_int(request.POST.get("section"))
        subject_id = _safe_int(request.POST.get("subject"))
        date_obj = _parse_date(request.POST.get("date"))

        if not class_id:
            messages.error(request, "Please choose a class before submitting.")
            return self.render_to_response(
                self.get_context_data(formset=formset)
            )

        if date_obj is None:
            messages.error(request, "Invalid date — use YYYY-MM-DD.")
            return self.render_to_response(
                self.get_context_data(formset=formset)
            )

        # FIX #4 — verify class exists and section belongs to it.
        cls = get_object_or_404(SchoolClass, pk=class_id)
        if section_id is not None and not Section.objects.filter(
            pk=section_id, school_class=cls
        ).exists():
            messages.error(request, "Selected section does not belong to the chosen class.")
            return self.render_to_response(
                self.get_context_data(formset=formset)
            )

        if not formset.is_valid():
            messages.error(request, "There were errors in the form.")
            return self.render_to_response(
                self.get_context_data(formset=formset)
            )

        # FIX #5 — reject students who aren't in the selected class. Without
        # this, a crafted POST can mark attendance for a student in another
        # class (or another school), polluting their record.
        allowed_student_ids = set(
            Student.objects
            .filter(current_class=cls)
            .values_list("pk", flat=True)
        )

        records = []
        for form in formset:
            cd = form.cleaned_data
            if not cd:
                continue
            sid = cd.get("student_id")
            if sid not in allowed_student_ids:
                messages.error(
                    request,
                    f"Student #{sid} is not in the selected class; attendance not saved.",
                )
                return self.render_to_response(
                    self.get_context_data(formset=formset)
                )
            records.append({
                "student_id": sid,
                "status": cd["status"],
                "notes": cd.get("notes", "") or "",
            })

        if not records:
            messages.warning(request, "No students to mark.")
            return redirect("attendance:daily_mark")

        try:
            n = AttendanceService.mark_attendance(
                school_class_id=class_id,
                section_id=section_id,
                date=date_obj,
                subject_id=subject_id,  # already None if blank
                records=records,
                user=request.user,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Attendance marking failed for class %s on %s", class_id, date_obj
            )
            messages.error(request, "Could not save attendance; please retry.")
            return self.render_to_response(
                self.get_context_data(formset=formset)
            )

        messages.success(request, f"Attendance marked for {n} student(s).")
        return redirect("attendance:daily_mark")


class AttendanceReportView(StaffRequiredMixin, ListView):
    template_name = "attendance/report.html"
    context_object_name = "records"
    paginate_by = 50

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            "student", "school_class", "academic_year"
        )

        class_id = _safe_int(self.request.GET.get("class"))
        if class_id is not None:
            qs = qs.filter(school_class_id=class_id)

        date_obj = _parse_date(self.request.GET.get("date"))
        if date_obj is not None:
            qs = qs.filter(date=date_obj)

        q = (self.request.GET.get("q") or "").strip()[:100]
        if q:
            # FIX #6 — Q() instead of `qs.filter(...) | qs.filter(...)`.
            # `|` drops `select_related` and can duplicate/UNION rows.
            qs = qs.filter(
                Q(student__full_name__icontains=q)
                | Q(student__registration_no__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [{"title": "Attendance Report"}]
        return ctx
