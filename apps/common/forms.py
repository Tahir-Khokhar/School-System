"""Common forms."""
from django import forms
from .models import AcademicYear, SchoolClass, Subject


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ["name", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class ClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "grade_level", "order", "is_active"]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "description", "is_compulsory", "is_active"]
