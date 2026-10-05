"""
Examination services — result calculation, grading, report card generation.
"""
from decimal import Decimal
from ..models import ClassTest, TestResult, ExamResult, TermResult, SurpriseTestResult


class ResultService:
    """All result calculation logic. The grade boundaries below can be made
    configurable via a GradeScheme model — for now they live in settings."""

    GRADE_BOUNDARIES = [
        (90, "A+"),
        (80, "A"),
        (70, "B"),
        (60, "C"),
        (50, "D"),
        (40, "E"),
        (0,  "F"),
    ]

    @classmethod
    def grade_for_percentage(cls, percentage) -> str:
        try:
            p = float(percentage)
        except (TypeError, ValueError):
            return "—"
        for threshold, grade in cls.GRADE_BOUNDARIES:
            if p >= threshold:
                return grade
        return "F"

    # -------------------------------------------------------------------
    # Calculate a student's class-test average for given subject + class
    # -------------------------------------------------------------------
    @classmethod
    def calculate_class_test_average(cls, student, academic_year, school_class, subject):
        results = TestResult.objects.filter(
            student=student,
            test__academic_year=academic_year,
            test__school_class=school_class,
            test__subject=subject,
            test__status="published",
        )
        if not results.count():
            return Decimal("0")
        total_obtained = sum(r.obtained_marks for r in results)
        total_max = sum(r.test.total_marks for r in results)
        if total_max == 0:
            return Decimal("0")
        return round((total_obtained / total_max) * 100, 2)

    # -------------------------------------------------------------------
    # Calculate term result
    # -------------------------------------------------------------------
    @classmethod
    def calculate_term_result(cls, student, academic_year, term, weights=None):
        """weights: dict like {'class_test': 0.2, 'exam': 0.6, 'homework': 0.2}"""
        weights = weights or {"class_test": 0.2, "exam": 0.6, "homework": 0.2}
        # Class test component
        ct_results = TestResult.objects.filter(
            student=student, test__academic_year=academic_year,
            test__status="published"
        )
        ct_avg = Decimal(0)
        if ct_results.count():
            ct_avg = sum(r.percentage for r in ct_results) / ct_results.count()

        # Exam component
        from .models import ExamResult, Exam
        ex_results = ExamResult.objects.filter(
            student=student, exam_subject__exam__academic_year=academic_year,
            exam_subject__exam__term=term,
        )
        ex_avg = Decimal(0)
        if ex_results.count():
            ex_avg = sum(
                (r.obtained_marks / r.exam_subject.total_marks) * 100 for r in ex_results
            ) / ex_results.count()

        # Homework component (placeholder — uses count of reviewed homeworks)
        from apps.homework.models import HomeworkSubmission
        hw_count = HomeworkSubmission.objects.filter(
            student=student, is_reviewed=True,
            homework__academic_year=academic_year,
        ).count()
        hw_avg = min(hw_count * 10, 100)

        percentage = (
            Decimal(weights["class_test"]) * Decimal(ct_avg) +
            Decimal(weights["exam"]) * Decimal(ex_avg) +
            Decimal(weights["homework"]) * Decimal(hw_avg)
        )

        obj, _ = TermResult.objects.update_or_create(
            student=student, academic_year=academic_year, term=term,
            defaults={
                "total_marks": Decimal(100),
                "obtained_marks": percentage,
                "percentage": percentage,
                "grade": cls.grade_for_percentage(float(percentage)),
                "status": TermResult.Status.SUBMITTED,
            },
        )
        return obj
