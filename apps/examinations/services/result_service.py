"""
Examination services — result calculation, grading, report card generation.
"""
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum

from ..models import ExamResult, TermResult, TestResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_decimal(value, default=Decimal("0")):
    if value is None or value == "":
        return default
    try:
        d = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default
    if d.is_nan() or d.is_infinite():
        return default
    return d


def _pct(obtained, total):
    """Return a quantized percentage Decimal, or 0 when total is 0."""
    total = _to_decimal(total)
    if not total:
        return Decimal("0.00")
    return (_to_decimal(obtained) / total * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


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

    DEFAULT_WEIGHTS = {
        "class_test": Decimal("0.2"),
        "exam": Decimal("0.6"),
        "homework": Decimal("0.2"),
    }

    # -------------------------------------------------------------------
    # Grading
    # -------------------------------------------------------------------
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
    # Class-test average (scoped: student + year + class + subject)
    # -------------------------------------------------------------------
    @classmethod
    def calculate_class_test_average(
        cls, student, academic_year, school_class, subject
    ):
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
        return _pct(agg["obtained"], agg["total"])

    # -------------------------------------------------------------------
    # Class-test average (year-scoped, used by term calc)
    # -------------------------------------------------------------------
    @classmethod
    def _class_test_avg_unscoped(cls, student, academic_year):
        agg = TestResult.objects.filter(
            student=student,
            test__academic_year=academic_year,
            test__status="published",
        ).aggregate(
            obtained=Sum("obtained_marks"),
            total=Sum("test__total_marks"),
        )
        return _pct(agg["obtained"], agg["total"])

    # -------------------------------------------------------------------
    # Exam component
    # -------------------------------------------------------------------
    @classmethod
    def calculate_exam_average(cls, student, academic_year, term, subject=None):
        """Average % across exam subjects for the given term.

        Rows whose subject has no `total_marks` are skipped — one bad
        subject must not abort the whole term calculation.
        """
        qs = ExamResult.objects.filter(
            student=student,
            exam_subject__exam__academic_year=academic_year,
            exam_subject__exam__term=term,
        ).select_related("exam_subject")

        if subject is not None:
            qs = qs.filter(exam_subject__subject=subject)

        obtained = Decimal("0")
        total = Decimal("0")
        for r in qs:
            subj_total = _to_decimal(getattr(r.exam_subject, "total_marks", None))
            if not subj_total:
                logger.warning(
                    "Skipping exam subject %s with total_marks=%r",
                    r.exam_subject_id, subj_total,
                )
                continue
            obtained += _to_decimal(r.obtained_marks)
            total += subj_total

        return _pct(obtained, total)

    # -------------------------------------------------------------------
    # Homework component
    # -------------------------------------------------------------------
    @classmethod
    def calculate_homework_component(cls, student, academic_year, target=10):
        """Map reviewed-homework count to 0–100, capped at 100.

        `target` is the number of reviewed submissions equal to 100%.
        """
        from apps.homework.models import HomeworkSubmission

        count = HomeworkSubmission.objects.filter(
            student=student,
            is_reviewed=True,
            homework__academic_year=academic_year,
        ).count()

        if target <= 0:
            return Decimal("0")
        return min(
            Decimal(count) * Decimal("100") / Decimal(target),
            Decimal("100"),
        )

    # -------------------------------------------------------------------
    # Term result (weighted aggregate)
    # -------------------------------------------------------------------
    @classmethod
    def calculate_term_result(
        cls, student, academic_year, term, weights=None, publish=False
    ):
        """Build or update a TermResult.

        - `weights` must sum to 1.0; pass None for defaults.
        - `publish=True` marks the result PUBLISHED.
        - Calling with `publish=False` never downgrades a PUBLISHED result.
        """
        weights = dict(weights or cls.DEFAULT_WEIGHTS)

        total_weight = sum(_to_decimal(v) for v in weights.values())
        if total_weight != Decimal("1"):
            raise ValueError(
                f"Result weights must sum to 1.0, got {total_weight}. "
                f"weights={weights}"
            )

        ct_avg = cls._class_test_avg_unscoped(student, academic_year)
        ex_avg = cls.calculate_exam_average(student, academic_year, term)
        hw_avg = cls.calculate_homework_component(student, academic_year)

        percentage = (
            _to_decimal(weights.get("class_test")) * ct_avg
            + _to_decimal(weights.get("exam")) * ex_avg
            + _to_decimal(weights.get("homework")) * hw_avg
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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

            if publish:
                if obj.status != TermResult.Status.PUBLISHED:
                    obj.status = TermResult.Status.PUBLISHED
                    obj.save(update_fields=["status"])
            elif created and obj.status != TermResult.Status.SUBMITTED:
                obj.status = TermResult.Status.SUBMITTED
                obj.save(update_fields=["status"])

        return obj

    # -------------------------------------------------------------------
    # Publish (idempotent)
    # -------------------------------------------------------------------
    @classmethod
    def publish_term_result(cls, term_result):
        """Return True if the status changed, False if already published."""
        if term_result.status == TermResult.Status.PUBLISHED:
            return False
        term_result.status = TermResult.Status.PUBLISHED
        term_result.save(update_fields=["status"])
        return True

    # -------------------------------------------------------------------
    # Report-card data
    # -------------------------------------------------------------------
    @classmethod
    def build_report_card_context(cls, term_result):
        """Return the context dict for the report-card template.

        Fails closed: a missing subject total produces a 0% line, never a
        crash.
        """
        student = term_result.student
        academic_year = term_result.academic_year
        term = term_result.term

        exam_results = (
            ExamResult.objects
            .filter(
                student=student,
                exam_subject__exam__academic_year=academic_year,
                exam_subject__exam__term=term,
            )
            .select_related("exam_subject", "exam_subject__subject")
            .order_by("exam_subject__subject__name")
        )

        subject_lines = []
        for r in exam_results:
            subj_total = _to_decimal(getattr(r.exam_subject, "total_marks", None))
            pct = _pct(r.obtained_marks, subj_total)
            subject_lines.append({
                "subject": (
                    r.exam_subject.subject.name
                    if r.exam_subject.subject_id else "—"
                ),
                "total_marks": subj_total,
                "obtained_marks": _to_decimal(r.obtained_marks),
                "percentage": pct,
                "grade": cls.grade_for_percentage(pct),
                "remarks": getattr(r, "remarks", "") or "",
            })

        return {
            "term_result": term_result,
            "student": student,
            "academic_year": academic_year,
            "term": term,
            "subject_lines": subject_lines,
            "percentage": _to_decimal(term_result.percentage),
            "grade": term_result.grade,
            "is_published": term_result.status == TermResult.Status.PUBLISHED,
        }
