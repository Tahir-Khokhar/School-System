"""
School ERP — students app.
Student + StudentEnrollment. The enrollment links a student to a class/section
in a given academic year, so historical records are preserved across years.
"""
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section
from apps.common.validators import validate_file_extension, validate_file_size


class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user", "parent", "current_class", "current_section")

    def active(self):
        return self.get_queryset().filter(status=Student.Status.ACTIVE)


class Student(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        GRADUATED = "graduated", "Graduated"
        TRANSFERRED = "transferred", "Transferred"
        EXPELLED = "expelled", "Expelled"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="student_profile",
    )
    registration_no = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    # CNIC/B-Form — unique ONLY when non-empty (a student without one
    # shouldn't be blocked from creation; the school office enters it later).
    cnic_or_bform = models.CharField(
        max_length=20, blank=True, db_index=True,
        help_text="CNIC for adults or B-Form for minors. Unique per student when non-empty.",
    )
    address = models.TextField(blank=True)
    previous_school = models.CharField(max_length=200, blank=True)
    previous_class = models.CharField(max_length=50, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    photograph = models.ImageField(
        upload_to="students/", blank=True, null=True,
        validators=[validate_file_extension, validate_file_size],
    )
    parent = models.ForeignKey(
        "parents.Parent", on_delete=models.PROTECT,
        related_name="children", null=True, blank=True,
    )
    current_class = models.ForeignKey(
        SchoolClass, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="students",
    )
    current_section = models.ForeignKey(
        Section, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="students",
    )
    admission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    blood_group = models.CharField(max_length=5, blank=True)
    medical_notes = models.TextField(blank=True)

    objects = StudentManager()

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["current_class", "current_section"]),
        ]
        constraints = [
            # Unique only when CNIC is provided. Multiple blank CNICs are
            # allowed (the school office enters CNIC/B-Form later).
            models.UniqueConstraint(
                fields=["cnic_or_bform"],
                condition=~models.Q(cnic_or_bform=""),
                name="unique_student_cnic_when_nonempty",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.registration_no})"

    @property
    def class_section_display(self):
        if self.current_class and self.current_section:
            return f"{self.current_class.name}-{self.current_section.name}"
        if self.current_class:
            return self.current_class.name
        return "—"


class StudentEnrollment(TimeStampedModel):
    """A record per student per academic year — preserves history."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="enrollments")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="enrollments")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="enrollments", null=True, blank=True)
    roll_no = models.CharField(max_length=10, blank=True)
    promotion_status = models.CharField(
        max_length=20,
        choices=[
            ("promoted", "Promoted"),
            ("conditional", "Promoted with Conditions"),
            ("repeated", "Repeated"),
            ("graduated", "Graduated"),
            ("transferred", "Transferred"),
        ],
        blank=True,
    )
    is_current = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "academic_year")
        ordering = ["-academic_year__start_date"]
        indexes = [
            models.Index(fields=["academic_year", "school_class"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.academic_year.name} — {self.school_class.name}"


# ---------------------------------------------------------------------------
# Registration number service
# Race-safe: transaction.atomic + select_for_update on the last-issued row.
# If two parallel requests reach generate() simultaneously, the row lock
# serializes them — the unique constraint on registration_no catches any
# remaining collision as a fallback IntegrityError.
# ---------------------------------------------------------------------------
class RegistrationNumberService:
    """SCH-<YEAR>-<6-digit sequence>"""

    @classmethod
    @transaction.atomic
    def generate(cls, year=None):
        year = year or timezone.now().year
        prefix = settings.SCHOOL_REGISTRATION_PREFIX
        pattern = f"{prefix}-{year}-"
        last = (
            Student.objects
            .select_for_update()
            .filter(registration_no__startswith=pattern)
            .order_by("-registration_no")
            .first()
        )
        if last:
            try:
                seq = int(last.registration_no.rsplit("-", 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{pattern}{seq:06d}"
