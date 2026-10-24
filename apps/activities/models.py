"""Activities — curricular, co-curricular, non-curricular + awards + certificates."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass
from apps.students.models import Student


class Activity(TimeStampedModel):
    class Category(models.TextChoices):
        CURRICULAR = "curricular", "Curricular"
        CO_CURRICULAR = "co_curricular", "Co-Curricular"
        NON_CURRICULAR = "non_curricular", "Non-Curricular"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="activities")
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.CO_CURRICULAR, db_index=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    classes = models.ManyToManyField(SchoolClass, related_name="activities", blank=True)
    location = models.CharField(max_length=200, blank=True)
    teacher_incharge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    result = models.TextField(blank=True)
    photo = models.ImageField(upload_to="activities/", blank=True, null=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Activities"


class StudentActivity(TimeStampedModel):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="participants")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="activities")
    position = models.CharField(max_length=50, blank=True)
    award = models.CharField(max_length=100, blank=True)
    certificate_no = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("activity", "student")


class Award(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="awards")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    certificate_no = models.CharField(max_length=50, blank=True)


class Certificate(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="certificates")
    title = models.CharField(max_length=200)
    issued_date = models.DateField()
    issued_by = models.CharField(max_length=200, blank=True)
    certificate_no = models.CharField(max_length=50, blank=True)
