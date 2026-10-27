from decimal import Decimal
from django import forms
from django.core.validators import MinValueValidator
from .models import Payroll, SalaryPayment


class PayrollForm(forms.ModelForm):
    """Payroll form — all money fields must be non-negative. The save()
    override clamps net_salary at zero so an over-deduction can never
    produce a negative payout.
    """
    # MinValueValidator(0) at the form level catches the bad input BEFORE
    # it reaches the model (cleaner error messages + no DB write attempt).
    basic_salary = forms.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    allowances = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        validators=[MinValueValidator(Decimal("0"))],
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    deductions = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        validators=[MinValueValidator(Decimal("0"))],
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    bonus = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        validators=[MinValueValidator(Decimal("0"))],
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    leave_deductions = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        validators=[MinValueValidator(Decimal("0"))],
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )

    class Meta:
        model = Payroll
        fields = ["teacher", "month", "basic_salary", "allowances", "deductions",
                  "bonus", "leave_deductions", "notes"]
        widgets = {"month": forms.TextInput(attrs={"placeholder": "e.g. October 2026"})}

    def clean(self):
        cleaned_data = super().clean()
        # Treat missing optional fields as zero (they're not required).
        for key in ("allowances", "deductions", "bonus", "leave_deductions"):
            if cleaned_data.get(key) is None:
                cleaned_data[key] = Decimal("0")
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Clamp each input at zero — even if MinValueValidator somehow missed it
        # (defense in depth).
        basic = max(Decimal("0"), obj.basic_salary or Decimal("0"))
        allowances = max(Decimal("0"), obj.allowances or Decimal("0"))
        deductions = min(obj.deductions or Decimal("0"), basic + allowances)  # can't exceed gross
        bonus = max(Decimal("0"), obj.bonus or Decimal("0"))
        leave_deductions = min(
            obj.leave_deductions or Decimal("0"),
            basic + allowances + bonus - deductions,  # can't exceed net positive
        )
        obj.basic_salary = basic
        obj.allowances = allowances
        obj.deductions = deductions
        obj.bonus = bonus
        obj.leave_deductions = leave_deductions
        # Net salary: never negative. If deductions exceed gross (which we
        # prevented by clamping above), the school office should reconcile
        # manually — a negative payroll must never be payable.
        net = basic + allowances - deductions + bonus - leave_deductions
        obj.net_salary = max(Decimal("0"), net)
        if commit:
            obj.save()
        return obj


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["method", "transaction_ref"]
