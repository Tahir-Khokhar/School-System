"""
School ERP — admissions app.
Full workflow: Application → Verification → Approval → Registration → Class assignment → Challan → Payment → Active Student
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section


class Admission(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        VERIFIED = "verified", "Verified"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REGISTERED = "registered", "Student Registered"
        COMPLETED = "completed", "Admission Completed"
        CANCELLED = "cancelled", "Cancelled"

    # Identifiers
    application_no = models.CharField(max_length=20, unique=True, db_index=True, editable=False)

    # Personal
    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("male","Male"),("female","Female")], default="male")
    cnic_bform = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Academic
    previous_school = models.CharField(max_length=200, blank=True)
    previous_class = models.CharField(max_length=50, blank=True)
    applying_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="admissions")
    applying_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name="admissions")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="admissions")
    admission_date = models.DateField(default=timezone.now)

    # Parent info (inline)
    parent_name = models.CharField(max_length=200, blank=True)
    parent_cnic = models.CharField(max_length=20, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    parent_occupation = models.CharField(max_length=100, blank=True)

    # Status / workflow
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)

    # Linked student once registered
    student = models.ForeignKey(
        "students.Student", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="admissions",
    )
    # Linked challan once generated
    admission_challan = models.ForeignKey(
        "fees.FeeChallan", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="admissions",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_admissions",
    )

    class Meta:
        ordering = ["-admission_date", "-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["academic_year", "applying_class"]),
        ]

    def __str__(self):
        return f"{self.application_no} — {self.full_name}"


class AdmissionDocument(TimeStampedModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to="admissions/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
    )

    def __str__(self):
        return f"{self.admission.application_no} — {self.name}"


# ---------------------------------------------------------------------------
# Application number generator + service
# ---------------------------------------------------------------------------
class ApplicationNumberService:
    @classmethod
    def generate(cls):
        year = timezone.now().year
        prefix = f"APP-{year}-"
        last = Admission.objects.filter(application_no__startswith=prefix).order_by("-application_no").first()
        if last:
            try:
                seq = int(last.application_no.rsplit("-", 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:05d}"
