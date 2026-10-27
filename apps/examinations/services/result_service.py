"""
Examination services — result calculation, grading, report card generation.
"""
from decimal import Decimal
from django.db import transaction
from ..models import ClassTest, TestResult, ExamResult, TermResult


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
    # Calculate a student's class-test average percentage for given
    # subject + class. Each test contributes proportional to its
    # total_marks — NOT a flat mean of percentages. A 10-mark quiz no
    # longer counts the same as a 100-mark term exam.
    # -------------------------------------------------------------------
    @classmethod
    def calculate_class_test_average(cls, student, academic_year, school_class, subject):
        results = TestResult.objects.filter(
            student=student,
            test__academic_year=academic_year,
            test__school_class=school_class,
            test__subject=subject,
            test__status="published",
        ).select_related("test")
        if not results.count():
            return Decimal("0")
        # Weighted by total_marks: sum(obtained) / sum(total) * 100
        total_obtained = sum(r.obtained_marks for r in results)
        total_max = sum(r.test.total_marks for r in results)
        if total_max == 0:
            return Decimal("0")
        # Decimal-safe: round to 2 decimal places.
        return Decimal(round((total_obtained / total_max) * 100, 2))

    # -------------------------------------------------------------------
    # Calculate term result — weighted average of class-test component,
    # exam component, and homework component. NEVER downgrades a
    # PUBLISHED result back to SUBMITTED.
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def calculate_term_result(cls, student, academic_year, term, weights=None):
        """weights: dict like {'class_test': 0.2, 'exam': 0.6, 'homework': 0.2}

        Race-safe: locks the (student, academic_year, term) row before
        writing. NEVER silently downgrades a PUBLISHED result — if the
        existing result is PUBLISHED, returns it unchanged (the school
        office must explicitly re-open it for editing).
        """
        weights = weights or {"class_test": Decimal("0.2"), "exam": Decimal("0.6"), "homework": Decimal("0.2")}

        # --- Lock existing row (if any) to serialize parallel recalcs. ---
        existing = (
            TermResult.objects
            .select_for_update()
            .filter(student=student, academic_year=academic_year, term=term)
            .first()
        )
        # --- Refuse to silently downgrade a published result. ---
        if existing and existing.status == TermResult.Status.PUBLISHED:
            return existing  # School office must explicitly re-open for edits.

        # --- Class-test component (weighted by total_marks, not flat mean) ---
        ct_results = TestResult.objects.filter(
            student=student, test__academic_year=academic_year,
            test__status="published"
        ).select_related("test")
        ct_pct = Decimal("0")
        if ct_results.count():
            ct_obtained = sum(r.obtained_marks for r in ct_results)
            ct_max = sum(r.test.total_marks for r in ct_results)
            if ct_max > 0:
                ct_pct = Decimal(round((ct_obtained / ct_max) * 100, 2))

        # --- Exam component (weighted by total_marks) ---
        ex_results = ExamResult.objects.filter(
            student=student, exam_subject__exam__academic_year=academic_year,
            exam_subject__exam__term=term,
        ).select_related("exam_subject")
        ex_pct = Decimal("0")
        if ex_results.count():
            ex_obtained = sum(r.obtained_marks for r in ex_results)
            ex_max = sum(r.exam_subject.total_marks for r in ex_results)
            if ex_max > 0:
                ex_pct = Decimal(round((ex_obtained / ex_max) * 100, 2))

        # --- Homework component (count of reviewed homeworks) ---
        from apps.homework.models import HomeworkSubmission
        hw_count = HomeworkSubmission.objects.filter(
            student=student, is_reviewed=True,
            homework__academic_year=academic_year,
        ).count()
        hw_pct = Decimal(min(hw_count * 10, 100))

        # --- Weighted total (Decimal-safe — never floats) ---
        ct_w = Decimal(weights.get("class_test", Decimal("0.2")))
        ex_w = Decimal(weights.get("exam", Decimal("0.6")))
        hw_w = Decimal(weights.get("homework", Decimal("0.2")))
        percentage = (
            ct_w * ct_pct +
            ex_w * ex_pct +
            hw_w * hw_pct
        )
        # Round to 2 decimal places.
        percentage = percentage.quantize(Decimal("0.01"))

        # Use the lock-protected row from above; create if absent.
        if existing:
            obj = existing
            obj.total_marks = Decimal(100)
            obj.obtained_marks = percentage
            obj.percentage = percentage
            obj.grade = cls.grade_for_percentage(float(percentage))
            # Don't downgrade an existing PUBLISHED result (already
            # checked above). New calculations land as SUBMITTED.
            obj.status = TermResult.Status.SUBMITTED
            obj.save(update_fields=[
                "total_marks", "obtained_marks", "percentage", "grade", "status",
            ])
        else:
            obj = TermResult.objects.create(
                student=student, academic_year=academic_year, term=term,
                total_marks=Decimal(100),
                obtained_marks=percentage,
                percentage=percentage,
                grade=cls.grade_for_percentage(float(percentage)),
                status=TermResult.Status.SUBMITTED,
            )
        return obj
