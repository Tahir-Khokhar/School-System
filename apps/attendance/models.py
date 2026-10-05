"""Attendance — students & teachers."""
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section, Subject
from apps.students.models import Student
from apps.teachers.models import Teacher


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        LEAVE = "leave", "Leave"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="attendance_records")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="attendance_records")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True, blank=True, related_name="attendance_records")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="marked_attendance",
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("student", "date", "subject")
        ordering = ["-date", "student__full_name"]
        indexes = [
            models.Index(fields=["academic_year", "school_class", "date"]),
            models.Index(fields=["student", "date"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.date} — {self.get_status_display()}"


class TeacherAttendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        LEAVE = "leave", "Leave"

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("teacher", "date")
        ordering = ["-date"]
        indexes = [models.Index(fields=["date", "status"])]


class AttendanceService:
    @classmethod
    @transaction.atomic
    def mark_attendance(cls, *, school_class_id, section_id, date, subject_id,
                       records, user, academic_year=None) -> int:
        """records = list of dicts {student_id, status, notes}."""
        if not academic_year:
            academic_year = AcademicYear.objects.get_active()
        count_created = 0
        for r in records:
            try:
                obj, created = Attendance.objects.update_or_create(
                    student_id=r["student_id"], date=date, subject_id=subject_id or None,
                    defaults={
                        "academic_year": academic_year,
                        "school_class_id": school_class_id,
                        "section_id": section_id,
                        "status": r["status"],
                        "marked_by": user,
                        "notes": r.get("notes", ""),
                    },
                )
                if created:
                    count_created += 1
            except Exception:
                continue
        return count_created

    @classmethod
    def get_student_attendance_percentage(cls, student, academic_year) -> float:
        total = Attendance.objects.filter(student=student, academic_year=academic_year).count()
        if not total:
            return 100.0
        present = Attendance.objects.filter(
            student=student, academic_year=academic_year,
            status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
        ).count()
        return round((present / total) * 100, 2)
