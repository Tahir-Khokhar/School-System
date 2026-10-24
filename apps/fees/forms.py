from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import FeeType, FeeStructure, FeeChallanItem, FeePayment


class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ["name", "code", "fee_type", "description", "default_amount", "is_active"]


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["academic_year", "school_class", "fee_type", "amount", "applies_monthly", "is_active"]


class FeeChallanItemForm(forms.ModelForm):
    class Meta:
        model = FeeChallanItem
        fields = ["fee_type", "description", "amount", "discount"]


class ChallanLookupForm(forms.Form):
    challan_no = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "e.g. CH-2026-000145",
            "autocomplete": "off",
        }),
    )


class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01,
                                widget=forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}))
    method = forms.ChoiceField(choices=[])  # populated in __init__
    transaction_ref = forms.CharField(required=False,
                                      widget=forms.TextInput(attrs={"class": "form-control"}))
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["method"].choices = FeePayment.PAYMENT_METHODS

    def clean_method(self):
        valid = dict(FeePayment.PAYMENT_METHODS).keys()
        if self.cleaned_data["method"] not in valid:
            raise forms.ValidationError("Invalid payment method.")
        return self.cleaned_data["method"]


class MonthlyChallanGenerateForm(forms.Form):
    school_class = forms.IntegerField(widget=forms.HiddenInput, required=False)
    month_label = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. October 2026",
        }),
    )
