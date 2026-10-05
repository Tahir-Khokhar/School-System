"""Student documents + ID cards."""
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.students.models import Student


class StudentDocument(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="student_documents/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]


class StudentIDCard(TimeStampedModel):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="id_card")
    card_no = models.CharField(max_length=30, unique=True)
    issued_date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
