"""Daily Diary — digital school diary."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section, Subject


class DiaryEntry(TimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="diary_entries")
    date = models.DateField(db_index=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="diary_entries")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name="diary_entries")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="diary_entries")
    topic = models.CharField(max_length=300)
    lecture_summary = models.TextField(blank=True)
    homework = models.TextField(blank=True)
    important_instructions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="diary_entries",
    )

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["school_class", "section", "date"])]

    def __str__(self):
        return f"{self.date} — {self.school_class.name} — {self.topic}"
