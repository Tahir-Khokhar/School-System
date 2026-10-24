"""
School ERP — fees app.
FeeType → FeeStructure → FeeChallan → FeeChallanItem → FeePayment → FeeReceipt
"""
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.common.models import TimeStampedModel, AcademicYear, SchoolClass
from apps.students.models import Student
from apps.teachers.models import Teacher


class FeeType(TimeStampedModel):
    FEE_TYPES = [
        ("tuition", "Tuition"),
        ("admission", "Admission"),
        ("annual", "Annual Charges"),
        ("examination", "Examination"),
        ("transport", "Transport"),
        ("library", "Library"),
        ("computer", "Computer"),
        ("sports", "Sports"),
        ("lab", "Lab"),
        ("uniform", "Uniform"),
        ("stationery", "Stationery"),
        ("fine", "Fine"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    fee_type = models.CharField(max_length=15, choices=FEE_TYPES, default="tuition", db_index=True)
    description = models.TextField(blank=True)
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class FeeStructure(TimeStampedModel):
    """Per-class fee template.Used by FeeService.generate_monthly_challans()."""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="fee_structures")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="fee_structures")
    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT, related_name="structures")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    applies_monthly = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("academic_year", "school_class", "fee_type")
        ordering = ["academic_year", "school_class", "fee_type"]


class FeeChallan(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partially Paid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    challan_no = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="fee_challans")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="fee_challans")
    month = models.CharField(max_length=20, blank=True, help_text="e.g. October 2026")
    due_date = models.DateField(null=True, blank=True)
    issue_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID, db_index=True)
    is_admission_challan = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_challans",
    )

    class Meta:
        ordering = ["-issue_date", "challan_no"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["academic_year", "month"]),
            models.Index(fields=["student", "academic_year"]),
        ]

    def __str__(self):
        return f"{self.challan_no} — {self.student.full_name}"

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items.all()) or Decimal("0")

    @property
    def late_fee(self):
        from apps.fees.services.fee_service import FeeService
        return FeeService.calculate_late_fee(self)

    @property
    def discount(self):
        return sum(item.discount for item in self.items.all()) or Decimal("0")

    @property
    def total_payable(self):
        return self.total_amount + self.late_fee - self.discount

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.filter(is_successful=True)) or Decimal("0")

    @property
    def balance(self):
        return self.total_payable - self.total_paid


class FeeChallanItem(TimeStampedModel):
    challan = models.ForeignKey(FeeChallan, on_delete=models.CASCADE, related_name="items")
    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ("challan", "fee_type")

    def __str__(self):
        return f"{self.challan.challan_no} — {self.fee_type.name} — {self.amount}"


class FeePayment(TimeStampedModel):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("card", "Card"),
        ("online", "Online"),
        ("other", "Other"),
    ]
    receipt_no = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    challan = models.ForeignKey(FeeChallan, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default="cash")
    transaction_ref = models.CharField(max_length=100, blank=True)
    is_successful = models.BooleanField(default=True, db_index=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_payments",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-payment_date", "-id"]
        indexes = [
            models.Index(fields=["is_successful", "payment_date"]),
            models.Index(fields=["challan"]),
        ]

    def __str__(self):
        return f"{self.receipt_no} — {self.amount}"

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = ReceiptNumberService.generate()
        super().save(*args, **kwargs)
        # Update challan status
        from apps.fees.services.fee_service import FeeService
        FeeService.update_challan_status(self.challan)


class ReceiptNumberService:
    @classmethod
    def generate(cls):
        year = timezone.now().year
        prefix = f"{settings.SCHOOL_RECEIPT_PREFIX}-{year}-"
        last = FeePayment.objects.filter(receipt_no__startswith=prefix).order_by("-receipt_no").first()
        if last:
            try:
                seq = int(last.receipt_no.rsplit("-", 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:05d}"


class ChallanNumberService:
    @classmethod
    def generate(cls):
        year = timezone.now().year
        prefix = f"{settings.SCHOOL_CHALLAN_PREFIX}-{year}-"
        last = FeeChallan.objects.filter(challan_no__startswith=prefix).order_by("-challan_no").first()
        if last:
            try:
                seq = int(last.challan_no.rsplit("-", 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"
