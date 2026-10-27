from datetime import datetime, timedelta
from django.contrib import messages
from apps.accounts.mixins import StaffRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, ListView, FormView

from apps.common.models import SchoolClass, Section, Subject, AcademicYear
from apps.students.models import Student
from .models import Attendance, AttendanceService
from .forms import AttendanceMarkFormSet, AttendanceFilterForm


class AttendanceMarkView(StaffRequiredMixin, PermissionRequiredMixin, TemplateView):
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

    def _validate_request(self, request):
        """Validate date + class_id + section_id + student_ids before any DB writes.

        Returns (ok: bool, error_msg: str, parsed: dict).
        """
        class_id = request.POST.get("school_class")
        section_id = request.POST.get("section")
        date_str = request.POST.get("date")
        subject_id = request.POST.get("subject") or None

        # Required fields.
        if not class_id or not date_str:
            return False, "Class and date are required.", {}
        # Parse date — reject retroactive tampering beyond a sensible window.
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return False, "Invalid date format.", {}
        today = timezone.now().date()
        # Block marking attendance for > 7 days in the future or > 30 days in the past.
        if date_obj > today + timedelta(days=7):
            return False, "Cannot mark attendance more than 7 days in the future.", {}
        if date_obj < today - timedelta(days=30):
            return False, "Cannot mark attendance more than 30 days in the past.", {}

        # Verify the class + section actually exist + match.
        cls = get_object_or_404(SchoolClass, pk=class_id)
        sec = Section.objects.filter(pk=section_id).first() if section_id else None
        if section_id and sec and sec.school_class_id != cls.pk:
            return False, "Section does not belong to the selected class.", {}

        return True, "", {
            "class": cls, "section": sec, "date_obj": date_obj, "subject_id": subject_id,
        }

    def post(self, request, *args, **kwargs):
        formset = AttendanceMarkFormSet(request.POST)
        if not formset.is_valid():
            messages.error(request, "There were errors in the form.")
            return self.render_to_response(self.get_context_data(formset=formset))

        # Validate date / class / section BEFORE any DB writes.
        ok, reason, parsed = self._validate_request(request)
        if not ok:
            messages.error(request, reason)
            return self.render_to_response(self.get_context_data(formset=formset))

        # Build records — but verify each student_id is actually enrolled in
        # the requested class+section (don't trust POST blindly).
        valid_student_ids = set(
            Student.objects.filter(
                current_class=parsed["class"],
                current_section=parsed["section"],
                status=Student.Status.ACTIVE,
            ).values_list("pk", flat=True)
        ) if parsed["section"] else set(
            Student.objects.filter(
                current_class=parsed["class"],
                status=Student.Status.ACTIVE,
            ).values_list("pk", flat=True)
        )

        records = []
        rejected = 0
        for form in formset:
            if not form.cleaned_data:
                continue
            sid = form.cleaned_data.get("student_id")
            status = form.cleaned_data.get("status")
            notes = form.cleaned_data.get("notes", "")
            # VALIDATE: student must actually be in this class+section.
            if sid not in valid_student_ids:
                rejected += 1
                continue
            # VALIDATE: status must be a known choice.
            valid_statuses = {s for s, _ in Attendance.Status.choices}
            if status not in valid_statuses:
                rejected += 1
                continue
            records.append({
                "student_id": sid, "status": status, "notes": notes,
            })

        if rejected:
            messages.warning(
                request,
                f"{rejected} record(s) rejected (student not in this class or invalid status).",
            )

        if not records:
            messages.error(request, "No valid attendance records to save.")
            return redirect("attendance:daily_mark")

        try:
            n = AttendanceService.mark_attendance(
                school_class_id=parsed["class"].pk,
                section_id=parsed["section"].pk if parsed["section"] else None,
                date=parsed["date_obj"],
                subject_id=parsed["subject_id"] or None,
                records=records, user=request.user,
            )
            messages.success(request, f"Attendance marked for {n} student(s).")
        except PermissionError as e:
            # Class-teacher rule blocked this submission.
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))
        # NOTE: deliberately NO bare `except Exception` — that would swallow
        # real bugs (e.g. IntegrityError on duplicate unique keys) and turn
        # them into silent 200-OK responses. Let those bubble up to Django's
        # 500 page so they're logged + visible.
        return redirect("attendance:daily_mark")


class AttendanceReportView(StaffRequiredMixin, ListView):
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
            except ValueError:
                # Invalid date format in query string — ignore the filter
                # rather than crashing the whole report. Other filters
                # (class, q) still apply.
                pass
        student_q = self.request.GET.get("q")
        if student_q:
            qs = (qs.filter(student__full_name__icontains=student_q)
                  | qs.filter(student__registration_no__icontains=student_q)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = SchoolClass.objects.filter(is_active=True)
        ctx["breadcrumbs"] = [{"title": "Attendance Report"}]
        return ctx
