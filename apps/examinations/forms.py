from django import forms
from django.forms import formset_factory, modelformset_factory
from .models import ClassTest, TestResult, SurpriseTest, Exam, ExamSubject, TermResult


class ClassTestForm(forms.ModelForm):
    class Meta:
        model = ClassTest
        fields = ["academic_year", "school_class", "section", "subject", "title",
                  "date", "total_marks", "passing_marks", "topics", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("total_marks")
        passing = cleaned.get("passing_marks")
        if total is not None and passing is not None and passing > total:
            raise forms.ValidationError(
                f"Passing marks ({passing}) cannot exceed total marks ({total})."
            )
        return cleaned


class SurpriseTestForm(forms.ModelForm):
    class Meta:
        model = SurpriseTest
        fields = ["academic_year", "school_class", "subject", "title",
                  "date", "total_marks", "topics", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["academic_year", "name", "term", "start_date", "end_date", "is_published"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError(
                "Exam end date cannot be earlier than the start date."
            )
        return cleaned


class ExamSubjectForm(forms.ModelForm):
    class Meta:
        model = ExamSubject
        fields = ["exam", "subject", "school_class", "date", "total_marks", "passing_marks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("total_marks")
        passing = cleaned.get("passing_marks")
        if total is not None and passing is not None and passing > total:
            raise forms.ValidationError(
                f"Passing marks ({passing}) cannot exceed total marks ({total})."
            )
        return cleaned


class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ["student", "obtained_marks", "remarks"]
        widgets = {"student": forms.HiddenInput}


TestResultFormSet = modelformset_factory(
    TestResult, fields=["student", "obtained_marks", "remarks"], extra=0
)


class TermResultForm(forms.ModelForm):
    class Meta:
        model = TermResult
        fields = ["status", "remarks", "teacher_remarks", "principal_remarks"]
