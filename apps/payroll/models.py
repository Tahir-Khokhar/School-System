from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone

TWO_DP = Decimal("0.01")


class PayrollService:
    SETTLED_STATUSES = (
        Payroll.Status.PAID,
        Payroll.Status.PROCESSING,
        Payroll.Status.FAILED,
    )

    @staticmethod
    def _dec(value) -> Decimal:
        if value in (None, ""):
            return Decimal("0.00")
        try:
            return Decimal(str(value)).quantize(TWO_DP, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0.00")

    @staticmethod
    def calculate_salary(teacher, month_label, *, allowances=None, deductions=None,
                         bonus=None, leave_deductions=None) -> dict:
        allowances = max(Decimal("0.00"), PayrollService._dec(allowances))
        deductions = max(Decimal("0.00"), PayrollService._dec(deductions))
        bonus = max(Decimal("0.00"), PayrollService._dec(bonus))
        leave_deductions = max(Decimal("0.00"), PayrollService._dec(leave_deductions))

        basic = PayrollService._dec(teacher.basic_salary)
        net = (basic + allowances - deductions + bonus - leave_deductions).quantize(TWO_DP)
        net = max(Decimal("0.00"), net)

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
    def generate_payroll(teacher, month_label, user=None, **kwargs) -> Payroll:
        data = PayrollService.calculate_salary(teacher, month_label, **kwargs)
        with transaction.atomic():
            existing = (
                Payroll.objects.select_for_update()
                .filter(teacher=teacher, month=month_label)
                .first()
            )
            if existing and existing.status in PayrollService.SETTLED_STATUSES:
                return existing

            defaults = {
                "basic_salary": data["basic_salary"],
                "allowances": data["allowances"],
                "deductions": data["deductions"],
                "bonus": data["bonus"],
                "leave_deductions": data["leave_deductions"],
                "net_salary": data["net_salary"],
                "status": Payroll.Status.DRAFT,
            }
            obj, _ = Payroll.objects.update_or_create(
                teacher=teacher, month=month_label, defaults=defaults,
            )
        return obj

    @staticmethod
    def record_bank_payment(payroll: Payroll, user, method="bank_transfer",
                            transaction_ref="", is_successful=True) -> SalaryPayment:
        with transaction.atomic():
            payroll = Payroll.objects.select_for_update().get(pk=payroll.pk)

            if payroll.status == Payroll.Status.DRAFT:
                raise ValueError("Cannot pay an unapproved payroll. Approve first.")
            if payroll.status == Payroll.Status.PAID:
                raise ValueError("This payroll has already been paid.")
            if payroll.status == Payroll.Status.PROCESSING:
                raise ValueError("Payroll is already being processed.")

            # Any previous (failed) attempt must be removed before re-creating —
            # SalaryPayment.payroll is a OneToOneField.
            if payroll.status == Payroll.Status.FAILED:
                SalaryPayment.objects.filter(payroll=payroll).delete()

            payment = SalaryPayment.objects.create(
                payroll=payroll,
                amount=payroll.net_salary,
                method=method,
                transaction_ref=transaction_ref,
                is_successful=is_successful,
                recorded_by=user,
                payment_date=timezone.now().date(),
            )
            payroll.status = (
                Payroll.Status.PAID if is_successful else Payroll.Status.FAILED
            )
            payroll.save(update_fields=["status"])

        payment.payroll = payroll  # keep callers' objects in sync
        return payment
