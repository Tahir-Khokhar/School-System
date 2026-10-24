"""School ERP — teachers app. Includes bank-info model treated as sensitive."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, SchoolClass, Section, Subject


class TeacherManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user")


class Teacher(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On Leave"
        RESIGNED = "resigned", "Resigned"

    class TeachingLevel(models.TextChoices):
        PRIMARY = "primary", "Primary (Grade 1-5)"
        MIDDLE = "middle", "Middle (Grade 6-8)"
        SECONDARY = "secondary", "Secondary (Grade 9-10)"
        ALL_LEVELS = "all", "All Levels"

    class StaffCategory(models.TextChoices):
        TEACHING = "teaching", "Teaching Staff"
        ADMIN = "admin", "Administration Staff"
        SUPPORT = "support", "Support Staff"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="teacher_profile",
    )
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)
    cnic = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("male","Male"),("female","Female")], default="male")
    contact_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    photograph = models.ImageField(upload_to="teachers/", blank=True, null=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    joining_date = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # NEW: teaching level + staff category
    teaching_level = models.CharField(
        max_length=12, choices=TeachingLevel.choices,
        default=TeachingLevel.ALL_LEVELS, db_index=True,
    )
    staff_category = models.CharField(
        max_length=10, choices=StaffCategory.choices,
        default=StaffCategory.TEACHING, db_index=True,
    )

    # ManyToMany — for teaching work assignment
    classes = models.ManyToManyField(SchoolClass, related_name="teachers", blank=True)
    sections = models.ManyToManyField(Section, related_name="teachers", blank=True)
    subjects = models.ManyToManyField(Subject, related_name="teachers", blank=True)

    objects = TeacherManager()

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["employee_id"]),
            models.Index(fields=["teaching_level", "staff_category"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"

    @property
    def display_label(self):
        """e.g. 'Mr. Ahmed Khan (EMP-0001 · Primary · Mathematics Teacher)'"""
        title = "Mr. " if self.gender == "male" else "Ms. "
        level = self.get_teaching_level_display().split(" (")[0]
        return f"{title}{self.full_name} — {self.employee_id} · {level} · {self.designation or self.staff_category}"


class TeacherBankInfo(TimeStampedModel):
    """Sensitive: only HR/payroll/super-admin roles should access."""
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, related_name="bank_info")
    bank_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=200, blank=True)
    account_title = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Teacher Bank Information"
        verbose_name_plural = "Teacher Bank Information"


# ---------------------------------------------------------------------------
# Employee ID generator
# ---------------------------------------------------------------------------
class EmployeeIDService:
    @classmethod
    def generate(cls):
        prefix = settings.SCHOOL_EMPLOYEE_PREFIX
        last = Teacher.objects.filter(employee_id__startswith=f"{prefix}-").order_by("-employee_id").first()
        if last:
            try:
                seq = int(last.employee_id.rsplit("-", 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}-{seq:04d}"
