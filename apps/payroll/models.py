"""
Payroll — kept separate from student fees.
Teacher → Payroll (monthly) → Salary Components → Salary Payment
"""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.teachers.models import Teacher


class Payroll(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="payrolls")
    month = models.CharField(max_length=20, db_index=True, help_text="e.g. October 2026")
    payment_month_date = models.DateField(null=True, blank=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leave_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approved_payrolls",
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("teacher", "month")
        ordering = ["-month", "teacher__full_name"]
        indexes = [models.Index(fields=["status", "month"])]


class SalaryPayment(TimeStampedModel):
    PAYMENT_METHODS = [
        ("bank_transfer", "Bank Transfer"),
        ("cash", "Cash"),
        ("cheque", "Cheque"),
        ("other", "Other"),
    ]
    payroll = models.OneToOneField(Payroll, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default="bank_transfer")
    transaction_ref = models.CharField(max_length=100, blank=True)
    is_successful = models.BooleanField(default=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-payment_date"]


class PayrollService:
    @staticmethod
    def calculate_salary(teacher: Teacher, month_label: str,
                          allowances=Decimal(0), deductions=Decimal(0),
                          bonus=Decimal(0), leave_deductions=Decimal(0)) -> dict:
        # VALIDATION: no negative values
        allowances = max(Decimal(0), Decimal(allowances))
        deductions = max(Decimal(0), Decimal(deductions))
        bonus = max(Decimal(0), Decimal(bonus))
        leave_deductions = max(Decimal(0), Decimal(leave_deductions))

        basic = teacher.basic_salary or Decimal(0)
        net = basic + allowances - deductions + bonus - leave_deductions
        # Net salary cannot be negative
        net = max(Decimal(0), net)
        return {
            "teacher": teacher,
            "month": month_label,
            "basic_salary": basic,
            "allowances": allowances,
            "deductions": deductions,
            "bonus": bonus,
            "leave_deductions": leave_deductions,
            "net_salary": net,
        }

    @staticmethod
    def generate_payroll(teacher: Teacher, month_label: str, user=None, **kwargs) -> Payroll:
        data = PayrollService.calculate_salary(teacher, month_label, **kwargs)
        # Don't overwrite a PAID or PROCESSING payroll
        existing = Payroll.objects.filter(teacher=teacher, month=month_label).first()
        if existing and existing.status in (Payroll.Status.PAID, Payroll.Status.PROCESSING):
            return existing  # Don't reset a paid payroll
        obj, created = Payroll.objects.update_or_create(
            teacher=teacher, month=month_label,
            defaults={
                "basic_salary": data["basic_salary"],
                "allowances": data["allowances"],
                "deductions": data["deductions"],
                "bonus": data["bonus"],
                "leave_deductions": data["leave_deductions"],
                "net_salary": data["net_salary"],
                "status": Payroll.Status.DRAFT,
            },
        )
        return obj

    @staticmethod
    def record_bank_payment(payroll: Payroll, user, method="bank_transfer",
                            transaction_ref="", is_successful=True) -> SalaryPayment:
        from django.db import transaction
        with transaction.atomic():
            payroll = Payroll.objects.select_for_update().get(pk=payroll.pk)

            # STATUS GUARD: can only pay APPROVED or FAILED payrolls
            if payroll.status == Payroll.Status.DRAFT:
                raise ValueError("Cannot pay an unapproved payroll. Approve first.")
            if payroll.status == Payroll.Status.PAID:
                raise ValueError("This payroll has already been paid.")

            # Delete any previous FAILED payment to allow retry
            if payroll.status == Payroll.Status.FAILED:
                SalaryPayment.objects.filter(payroll=payroll, is_successful=False).delete()

            payment = SalaryPayment.objects.create(
                payroll=payroll, amount=payroll.net_salary,
                method=method, transaction_ref=transaction_ref,
                is_successful=is_successful, recorded_by=user,
            )
            payroll.status = Payroll.Status.PAID if is_successful else Payroll.Status.FAILED
            payroll.save(update_fields=["status"])
        return payment
