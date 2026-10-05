"""Date sheets."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Subject


class DateSheet(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="datesheets")
    title = models.CharField(max_length=200)
    term = models.CharField(max_length=10, choices=[
        ("first", "First Term"), ("mid", "Mid Term"),
        ("second", "Second Term"), ("final", "Final Term"),
    ], default="first")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="datesheets")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-academic_year", "school_class"]


class DateSheetItem(TimeStampedModel):
    datesheet = models.ForeignKey(DateSheet, on_delete=models.CASCADE, related_name="items")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    instructions = models.TextField(blank=True)

    class Meta:
        ordering = ["date", "start_time"]
