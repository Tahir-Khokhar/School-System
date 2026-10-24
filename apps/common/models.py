"""
School ERP — common app.
Shared models: AcademicYear, School, SchoolClass, Section, Subject.
Plus the school context processor used everywhere in templates.
"""
from django.db import models
from django.core.cache import cache
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AcademicYearManager(models.Manager):
    def get_active(self):
        cached = cache.get("active_academic_year_id")
        if cached:
            return self.get_queryset().filter(pk=cached).first()
        active = self.get_queryset().filter(is_active=True).first()
        if active:
            cache.set("active_academic_year_id", active.pk, 60 * 60)
        return active


class AcademicYear(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2026–2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, db_index=True)
    is_archived = models.BooleanField(default=False)

    objects = AcademicYearManager()

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # only one active year at a time
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        cache.delete("active_academic_year_id")
        super().save(*args, **kwargs)


class School(TimeStampedModel):
    name = models.CharField(max_length=200, default=settings.SCHOOL_NAME)
    tagline = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="school/", blank=True, null=True)

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def __str__(self):
        return self.name


class SchoolClass(TimeStampedModel):
    GRADE_LEVELS = [
        ("pre", "Pre-Primary"),
        ("primary", "Primary"),
        ("middle", "Middle"),
        ("secondary", "Secondary"),
        ("higher", "Higher Secondary"),
    ]
    name = models.CharField(max_length=20, unique=True, help_text="e.g. Grade 8")
    grade_level = models.CharField(max_length=10, choices=GRADE_LEVELS, default="middle")
    order = models.PositiveIntegerField(default=0, help_text="Sort order")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name


class Section(TimeStampedModel):
    class SubjectGroup(models.TextChoices):
        NONE = "", "—"
        COMPUTER = "computer", "Computer Science"
        BIO = "bio", "Biology"
        PRE_MEDICAL = "pre_med", "Pre-Medical"
        PRE_ENGINEERING = "pre_eng", "Pre-Engineering"
        GENERAL = "general", "General"

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=10, help_text="e.g. A, B, C")
    capacity = models.PositiveIntegerField(default=40)
    subject_group = models.CharField(
        max_length=10, choices=SubjectGroup.choices,
        default=SubjectGroup.NONE, blank=True, db_index=True,
        help_text="For Grade 9-10: Computer or Biology; lower grades leave as '—'.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("school_class", "name")
        ordering = ["school_class__order", "name"]

    def __str__(self):
        return f"{self.school_class.name}-{self.name}"

    @property
    def display_name(self):
        """Friendly name including subject group, e.g. 'Grade 9-A (Computer)'"""
        if self.subject_group:
            return f"{self.school_class.name}-{self.name} ({self.get_subject_group_display()})"
        return f"{self.school_class.name}-{self.name}"

    @property
    def student_count(self):
        from apps.students.models import Student
        return Student.objects.filter(current_section=self, status=Student.Status.ACTIVE).count()


class Subject(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_compulsory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ---------------------------------------------------------------------------
# Helper used by templates: school context processor + active year lookup
# ---------------------------------------------------------------------------
def get_active_academic_year():
    return AcademicYear.objects.get_active()
