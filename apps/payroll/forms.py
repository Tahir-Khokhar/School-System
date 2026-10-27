"""Payroll forms."""
from decimal import Decimal

from django import forms

from .models import Payroll, SalaryPayment


def _dec(value):
    """Return value as Decimal, or 0 if None/invalid."""
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = [
            "teacher", "month", "basic_salary", "allowances", "deductions",
            "bonus", "leave_deductions", "notes",
        ]
        widgets = {
            "month": forms.TextInput(attrs={"placeholder": "e.g. October 2026"}),
        }

    def clean(self):
        cleaned = super().clean()

        basic = _dec(cleaned.get("basic_salary"))
        allowances = _dec(cleaned.get("allowances"))
        deductions = _dec(cleaned.get("deductions"))
        bonus = _dec(cleaned.get("bonus"))
        leave = _dec(cleaned.get("leave_deductions"))

        # FIX #1 — negative money values are never valid. Reject them
        # explicitly instead of letting the model accept them and storing
        # a net_salary of e.g. -500.
        for field_name, value in (
            ("basic_salary", basic),
            ("allowances", allowances),
            ("deductions", deductions),
            ("bonus", bonus),
            ("leave_deductions", leave),
        ):
            if value < 0:
                self.add_error(field_name, "Must not be negative.")

        # FIX #2 — total deductions must not exceed total earnings,
        # otherwise the teacher owes the school money. Catch it here with
        # a clear message instead of a mysterious negative net_salary.
        total_earnings = basic + allowances + bonus
        total_deductions = deductions + leave
        if total_earnings and total_deductions > total_earnings:
            self.add_error(
                None,
                "Total deductions exceed total earnings "
                f"(earnings {total_earnings}, deductions {total_deductions}).",
            )

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        # FIX #3 — compute net_salary from validated cleaned_data, not from
        # the raw instance, so the value matches what clean() validated.
        # Also, only assign when the form actually has that data (avoids
        # overwriting with 0 when a partial save happens — though partial
        # saves are prevented by commit=True below).
        obj.net_salary = (
            _dec(self.cleaned_data.get("basic_salary"))
            + _dec(self.cleaned_data.get("allowances"))
            + _dec(self.cleaned_data.get("bonus"))
            - _dec(self.cleaned_data.get("deductions"))
            - _dec(self.cleaned_data.get("leave_deductions"))
        )
        if commit:
            obj.save()
        return obj


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["method", "transaction_ref"]

    def clean_transaction_ref(self):
        # FIX #4 — transaction_ref is required for non-cash methods.
        # Cash payments don't need one, but "bank transfer" / "cheque" /
        # "online" without a reference makes reconciliation impossible.
        ref = (self.cleaned_data.get("transaction_ref") or "").strip()
        method = (self.cleaned_data.get("method") or "").strip().lower()
        if not ref and method not in ("", "cash"):
            raise forms.ValidationError(
                "Transaction reference is required for non-cash payments."
            )
        return ref
