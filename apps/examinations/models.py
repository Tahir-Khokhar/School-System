"""
Examinations — class tests, surprise tests, term exams, exam results, term results.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass, Section, Subject
from apps.students.models import Student


class ClassTest(TimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="class_tests")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="class_tests")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name="class_tests")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="class_tests")
    title = models.CharField(max_length=200)
    date = models.DateField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    topics = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=[("draft","Draft"),("published","Published")], default="draft", db_index=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["school_class", "subject", "date"])]


class TestResult(TimeStampedModel):
    test = models.ForeignKey(ClassTest, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="test_results")
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("test", "student")

    @property
    def percentage(self):
        if self.test.total_marks == 0:
            return Decimal("0")
        return round((self.obtained_marks / self.test.total_marks) * 100, 2)

    @property
    def grade(self):
        from apps.examinations.services import ResultService
        return ResultService.grade_for_percentage(self.percentage)

    @property
    def is_pass(self):
        return self.obtained_marks >= self.test.passing_marks


class SurpriseTest(TimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="surprise_tests")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="surprise_tests")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="surprise_tests")
    title = models.CharField(max_length=200)
    date = models.DateField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    topics = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=[("draft","Draft"),("published","Published")], default="draft", db_index=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


class SurpriseTestResult(TimeStampedModel):
    test = models.ForeignKey(SurpriseTest, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="surprise_test_results")
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("test", "student")


class Exam(TimeStampedModel):
    """Term exam (First/Second/Mid/Final)."""
    class Term(models.TextChoices):
        FIRST = "first", "First Term"
        SECOND = "second", "Second Term"
        MID = "mid", "Mid Term"
        FINAL = "final", "Final Term"

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="exams")
    name = models.CharField(max_length=200)
    term = models.CharField(max_length=10, choices=Term.choices, default=Term.FIRST)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]


class ExamSubject(TimeStampedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    date = models.DateField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2, default=40)


class ExamResult(TimeStampedModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_results")
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)


class TermResult(TimeStampedModel):
    """Aggregated result for a student per academic year per term."""
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        PUBLISHED = "published", "Published"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="term_results")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="term_results")
    term = models.CharField(max_length=10, choices=Exam.Term.choices)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=5, blank=True)
    rank = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    remarks = models.TextField(blank=True)
    teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("student", "academic_year", "term")
        ordering = ["-percentage"]
