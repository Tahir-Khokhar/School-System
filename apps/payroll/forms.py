from django import forms
from .models import Payroll, SalaryPayment


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ["teacher", "month", "basic_salary", "allowances", "deductions",
                  "bonus", "leave_deductions", "notes"]
        widgets = {"month": forms.TextInput(attrs={"placeholder": "e.g. October 2026"})}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.net_salary = (
            obj.basic_salary + obj.allowances + obj.bonus - obj.deductions - obj.leave_deductions
        )
        if commit:
            obj.save()
        return obj


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["method", "transaction_ref"]
