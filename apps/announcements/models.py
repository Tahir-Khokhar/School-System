from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section


class Announcement(TimeStampedModel):
    class Audience(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        TEACHERS = "teachers", "Teachers"
        STUDENTS = "students", "Students"
        PARENTS = "parents", "Parents"
        CLASS = "class", "Specific Class"
        SECTION = "section", "Specific Section"
        ADMIN = "admin", "Administration"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, null=True, blank=True, related_name="announcements")
    title = models.CharField(max_length=200)
    description = models.TextField()
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.EVERYONE)
    target_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True)
    target_section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    attachment = models.FileField(upload_to="announcements/", blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-publish_date"]
        indexes = [models.Index(fields=["is_published", "audience"])]
