from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name", "father_name", "mother_name", "date_of_birth", "gender",
            "cnic_or_bform", "address", "previous_school", "previous_class",
            "contact_phone", "email", "parent", "current_class", "current_section",
            "admission_date", "status", "blood_group", "medical_notes",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "admission_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "medical_notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
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
                Column("cnic_or_bform", css_class="col-md-4"),
                Column("contact_phone", css_class="col-md-4"),
                Column("email", css_class="col-md-4"),
            ),
            Row(
                Column("current_class", css_class="col-md-4"),
                Column("current_section", css_class="col-md-4"),
                Column("parent", css_class="col-md-4"),
            ),
            Row(
                Column("admission_date", css_class="col-md-4"),
                Column("blood_group", css_class="col-md-4"),
                Column("status", css_class="col-md-4"),
            ),
            "address",
            Row(
                Column("previous_school", css_class="col-md-6"),
                Column("previous_class", css_class="col-md-6"),
            ),
            "medical_notes",
        )
