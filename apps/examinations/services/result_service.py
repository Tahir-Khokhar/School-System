"""
Examination services — result calculation, grading, report card generation.
"""
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Count, Q

from ..models import (
    ClassTest, TestResult, ExamResult, TermResult, SurpriseTestResult,
)

logger = logging.getLogger(__name__)


# Safe conversion helper used throughout.
def _to_decimal(value, default=Decimal("0")):
    if value is None or value == "":
        return default
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


class ResultService:
    """All result calculation logic.

    The grade boundaries below could be moved into a GradeScheme model later.
    """

    GRADE_BOUNDARIES = [
        (Decimal("90"), "A+"),
        (Decimal("80"), "A"),
        (Decimal("70"), "B"),
        (Decimal("60"), "C"),
        (Decimal("50"), "D"),
        (Decimal("40"), "E"),
        (Decimal("0"), "F"),
    ]

    @classmethod
    def grade_for_percentage(cls, percentage) -> str:
        try:
            p = Decimal(str(percentage))
        except (InvalidOperation, TypeError, ValueError):
            return "—"
        if p.is_nan() or p.is_infinite():
            return "—"
        for threshold, grade in cls.GRADE_BOUNDARIES:
            if p >= threshold:
                return grade
        return "F"

    # -------------------------------------------------------------------
    # Class-test average
    # -------------------------------------------------------------------
    @classmethod
    def calculate_class_test_average(
        cls, student, academic_year, school_class, subject
    ):
        # FIX #1 — aggregate in the DB instead of iterating results one by
        # one in Python. `count()` and Python-side sums are N+1 queries.
        from django.db.models import Sum, F

        agg = TestResult.objects.filter(
            student=student,
            test__academic_year=academic_year,
            test__school_class=school_class,
            test__subject=subject,
            test__status="published",
        ).aggregate(
            obtained=Sum("obtained_marks"),
            total=Sum("test__total_marks"),
        )

        obtained = agg["obtained"] or Decimal("0")
        total = agg["total"] or Decimal("0")

        if not total:
            return Decimal("0")
        return (obtained / total * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    # -------------------------------------------------------------------
    # Term result
    # -------------------------------------------------------------------
    @classmethod
    def calculate_term_result(cls, student, academic_year, term, weights=None):
        """weights: dict like {'class_test': 0.2, 'exam': 0.6, 'homework': 0.2}

        Weights are validated: they must sum to 1.0. If they don't, the
        caller gets a clear error instead of a silently wrong percentage.
        """
        weights = weights or {"class_test": 0.2, "exam": 0.6, "homework": 0.2}

        # FIX #2 — validate weights instead of trusting caller input.
        # Otherwise a caller passing {'class_test': 1, 'exam': 1, 'homework': 1}
        # produces a 300% final percentage with no warning.
        total_weight = (
            _to_decimal(weights.get("class_test"))
            + _to_decimal(weights.get("exam"))
            + _to_decimal(weights.get("homework"))
        )
        if total_weight != Decimal("1"):
            raise ValueError(
                f"Result weights must sum to 1.0, got {total_weight}. "
                f"weights={weights}"
            )

        # --- Class-test component -------------------------------------
        ct_agg = TestResult.objects.filter(
            student=student,
            test__academic_year=academic_year,
            test__status="published",
        ).aggregate(
            obtained=Sum("obtained_marks"),
            total=Sum("test__total_marks"),
        )
        ct_obtained = ct_agg["obtained"] or Decimal("0")
        ct_total = ct_agg["total"] or Decimal("0")
        ct_avg = (
            (ct_obtained / ct_total * Decimal("100")) if ct_total else Decimal("0")
        )

        # --- Exam component -------------------------------------------
        ex_results = ExamResult.objects.filter(
            student=student,
            exam_subject__exam__academic_year=academic_year,
            exam_subject__exam__term=term,
        )
        # FIX #3 — division by zero when an exam subject has total_marks=0
        # (or NULL). Skip those rows instead of crashing the whole term
        # calculation.
        ex_obtained = Decimal("0")
        ex_total = Decimal("0")
        for r in ex_results:
            subj_total = _to_decimal(getattr(r.exam_subject, "total_marks", None))
            if not subj_total:
                logger.warning(
                    "Skipping exam subject %s with total_marks=%r in term calc",
                    r.exam_subject_id, subj_total,
                )
                continue
            ex_obtained += _to_decimal(r.obtained_marks)
            ex_total += subj_total
        ex_avg = (ex_obtained / ex_total * Decimal("100")) if ex_total else Decimal("0")

        # --- Homework component ---------------------------------------
        from apps.homework.models import HomeworkSubmission
        hw_count = HomeworkSubmission.objects.filter(
            student=student,
            is_reviewed=True,
            homework__academic_year=academic_year,
        ).count()
        hw_avg = min(hw_count * 10, 100)

        percentage = (
            _to_decimal(weights["class_test"]) * ct_avg
            + _to_decimal(weights["exam"]) * ex_avg
            + _to_decimal(weights["homework"]) * Decimal(hw_avg)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # FIX #4 — re-running this must not lose an already-published status.
        # `update_or_create` with `status=SUBMITTED` in defaults downgrades a
        # published result back to submitted.
        with transaction.atomic():
            obj, created = TermResult.objects.update_or_create(
                student=student,
                academic_year=academic_year,
                term=term,
                defaults={
                    "total_marks": Decimal("100"),
                    "obtained_marks": percentage,
                    "percentage": percentage,
                    "grade": cls.grade_for_percentage(percentage),
                },
            )
            # Only set the status when this is a new record or when the
            # existing one isn't already published.
            if created or obj.status != TermResult.Status.PUBLISHED:
                if obj.status != TermResult.Status.SUBMITTED:
                    obj.status = TermResult.Status.SUBMITTED
                    obj.save(update_fields=["status"])

        return obj
