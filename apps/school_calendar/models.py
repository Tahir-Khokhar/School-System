from django.db import models
from apps.common.models import TimeStampedModel, AcademicYear


class CalendarEvent(TimeStampedModel):
    class Category(models.TextChoices):
        HOLIDAY = "holiday", "Holiday"
        EXAM = "exam", "Exam"
        TEST = "test", "Test"
        PARENT_MEETING = "parent_meeting", "Parent Meeting"
        EVENT = "event", "Event"
        SPORTS_DAY = "sports_day", "Sports Day"
        ANNUAL_FUNCTION = "annual_function", "Annual Function"
        TRIP = "trip", "Trip"
        DEADLINE = "deadline", "Deadline"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, null=True, blank=True, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.EVENT)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_date"]
