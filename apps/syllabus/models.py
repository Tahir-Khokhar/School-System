"""Syllabus + lecture planning + progress tracking."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Subject


class Syllabus(TimeStampedModel):
    class Term(models.TextChoices):
        FIRST = "first", "First Term"
        SECOND = "second", "Second Term"
        FINAL = "final", "Final Term"
        MID = "mid", "Mid Term"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="syllabi")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="syllabi")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="syllabi")
    term = models.CharField(max_length=10, choices=Term.choices, default=Term.FIRST)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("academic_year", "school_class", "subject", "term")
        ordering = ["academic_year", "school_class", "term", "subject"]

    def __str__(self):
        return f"{self.school_class.name} — {self.subject.name} — {self.get_term_display()}"


class SyllabusTopic(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        DELAYED = "delayed", "Delayed"

    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name="topics")
    chapter = models.CharField(max_length=200)
    topic = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    priority = models.PositiveIntegerField(default=3, help_text="1=High, 5=Low")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NOT_STARTED, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["syllabus", "priority", "id"]
        indexes = [models.Index(fields=["status"])]


class LecturePlan(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLANNED = "planned", "Planned"
        COMPLETED = "completed", "Completed"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="lecture_plans")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="lecture_plans")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lecture_plans")
    topic = models.CharField(max_length=300)
    date = models.DateField()
    learning_objectives = models.TextField(blank=True)
    lecture_content = models.TextField(blank=True)
    activities = models.TextField(blank=True)
    homework = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    estimated_duration = models.PositiveIntegerField(default=40, help_text="in minutes")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="lecture_plans")

    class Meta:
        ordering = ["-date"]


class SyllabusProgressService:
    @staticmethod
    def get_progress(syllabus: Syllabus) -> dict:
        topics = syllabus.topics.all()
        total = topics.count()
        completed = topics.filter(status=SyllabusTopic.Status.COMPLETED).count()
        in_progress = topics.filter(status=SyllabusTopic.Status.IN_PROGRESS).count()
        delayed = topics.filter(status=SyllabusTopic.Status.DELAYED).count()
        not_started = topics.filter(status=SyllabusTopic.Status.NOT_STARTED).count()
        percentage = round((completed / total * 100), 2) if total else 0.0
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "delayed": delayed,
            "not_started": not_started,
            "remaining": total - completed,
            "percentage": percentage,
        }
