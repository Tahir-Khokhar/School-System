from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Admission


class AdmissionForm(forms.ModelForm):
    """Multi-step style form (Personal + Parent + Academic)."""
    class Meta:
        model = Admission
        fields = [
            "full_name", "father_name", "mother_name", "date_of_birth", "gender",
            "cnic_bform", "address", "contact_phone", "email",
            "previous_school", "previous_class",
            "applying_class", "applying_section", "academic_year", "admission_date",
            "parent_name", "parent_cnic", "parent_phone", "parent_occupation",
            "notes",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "admission_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            # Personal Info
            Row(
                Column("full_name", css_class="col-md-6"),
                Column("father_name", css_class="col-md-6"),
            ),
            Row(
                Column("mother_name", css_class="col-md-6"),
                Column("date_of_birth", css_class="col-md-3"),
                Column("gender", css_class="col-md-3"),
            ),
            Row(
                Column("cnic_bform", css_class="col-md-4"),
                Column("contact_phone", css_class="col-md-4"),
                Column("email", css_class="col-md-4"),
            ),
            "address",
            # Academic
            Row(
                Column("previous_school", css_class="col-md-6"),
                Column("previous_class", css_class="col-md-6"),
            ),
            Row(
                Column("applying_class", css_class="col-md-4"),
                Column("applying_section", css_class="col-md-4"),
                Column("academic_year", css_class="col-md-4"),
            ),
            Row(
                Column("admission_date", css_class="col-md-6"),
            ),
            # Parent
            Row(
                Column("parent_name", css_class="col-md-6"),
                Column("parent_cnic", css_class="col-md-6"),
            ),
            Row(
                Column("parent_phone", css_class="col-md-6"),
                Column("parent_occupation", css_class="col-md-6"),
            ),
            "notes",
        )


class AdmissionStatusForm(forms.Form):
    """Single-field form used by the workflow action pages."""
    notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Add a review note (optional)."
    )
