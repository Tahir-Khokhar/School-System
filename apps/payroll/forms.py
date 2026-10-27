"""Payroll forms."""
from decimal import Decimal, InvalidOperation

from django import forms

from .models import Payroll, SalaryPayment


ZERO = Decimal("0")


def _dec(value):
    """Return value as Decimal, or 0 if None/blank/invalid."""
    if value in (None, ""):
        return ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return ZERO


class PayrollForm(forms.ModelForm):
    MONEY_FIELDS = (
        "basic_salary",
        "allowances",
        "deductions",
        "bonus",
        "leave_deductions",
    )

    class Meta:
        model = Payroll
        fields = [
            "teacher",
            "month",
            *MONEY_FIELDS,
            "notes",
        ]
        widgets = {
            "month": forms.TextInput(attrs={"placeholder": "e.g. October 2026"}),
        }

    def clean(self):
        cleaned = super().clean()

        money = {name: _dec(cleaned.get(name)) for name in self.MONEY_FIELDS}

        for name, value in money.items():
            if value < ZERO:
                self.add_error(name, "Must not be negative.")

        earnings = money["basic_salary"] + money["allowances"] + money["bonus"]
        deductions = money["deductions"] + money["leave_deductions"]

        if deductions > earnings:
            self.add_error(
                "__all__",
                "Total deductions exceed total earnings "
                f"(earnings {earnings}, deductions {deductions}).",
            )

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        d = self.cleaned_data
        obj.net_salary = (
            _dec(d.get("basic_salary"))
            + _dec(d.get("allowances"))
            + _dec(d.get("bonus"))
            - _dec(d.get("deductions"))
            - _dec(d.get("leave_deductions"))
        )
        if commit:
            obj.save()
        return obj


class SalaryPaymentForm(forms.ModelForm):
    CASH_METHODS = {"cash", ""}

    class Meta:
        model = SalaryPayment
        fields = ["method", "transaction_ref"]

    def clean_transaction_ref(self):
        ref = (self.cleaned_data.get("transaction_ref") or "").strip()
        # ``method`` may be absent if its own field validation failed.
        method = (self.cleaned_data.get("method") or "").strip().lower()
        if not ref and method not in self.CASH_METHODS:
            raise forms.ValidationError(
                "Transaction reference is required for non-cash payments."
            )
        return ref
