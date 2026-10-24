from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section, Subject
from apps.students.models import Student


class Homework(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ASSIGNED = "assigned", "Assigned"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        CLOSED = "closed", "Closed"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="homeworks")
    title = models.CharField(max_length=200)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="homeworks")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name="homeworks")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="homeworks")
    description = models.TextField()
    assigned_date = models.DateField()
    due_date = models.DateField()
    attachment = models.FileField(upload_to="homework/", blank=True, null=True)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="assigned_homeworks")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ASSIGNED, db_index=True)

    class Meta:
        ordering = ["-due_date"]
        indexes = [models.Index(fields=["school_class", "due_date"])]


class HomeworkSubmission(TimeStampedModel):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="homework_submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="homework_submissions/", blank=True, null=True)
    text = models.TextField(blank=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("homework", "student")
        ordering = ["-submitted_at"]
