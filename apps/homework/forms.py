from django import forms
from .models import Homework, HomeworkSubmission


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ["academic_year", "title", "school_class", "section", "subject",
                  "description", "assigned_date", "due_date", "attachment", "total_marks", "status"]
        widgets = {
            "assigned_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ["text", "file", "marks", "feedback"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3}), "feedback": forms.Textarea(attrs={"rows": 2})}
