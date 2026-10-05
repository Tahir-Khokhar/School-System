from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Teacher, TeacherBankInfo


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "full_name", "father_name", "cnic", "date_of_birth", "gender",
            "contact_phone", "email", "address", "qualification",
            "experience_years", "joining_date", "designation", "status",
            "basic_salary", "classes", "sections", "subjects",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
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
                Column("cnic", css_class="col-md-4"),
                Column("date_of_birth", css_class="col-md-4"),
                Column("gender", css_class="col-md-4"),
            ),
            Row(
                Column("contact_phone", css_class="col-md-4"),
                Column("email", css_class="col-md-4"),
                Column("status", css_class="col-md-4"),
            ),
            Row(
                Column("qualification", css_class="col-md-6"),
                Column("experience_years", css_class="col-md-3"),
                Column("joining_date", css_class="col-md-3"),
            ),
            Row(
                Column("designation", css_class="col-md-6"),
                Column("basic_salary", css_class="col-md-6"),
            ),
            "address",
            Row(
                Column("classes", css_class="col-md-4"),
                Column("sections", css_class="col-md-4"),
                Column("subjects", css_class="col-md-4"),
            ),
        )


class TeacherBankInfoForm(forms.ModelForm):
    class Meta:
        model = TeacherBankInfo
        fields = ["bank_name", "branch", "account_title", "account_number", "iban", "swift_code"]
