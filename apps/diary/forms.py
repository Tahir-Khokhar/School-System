from django import forms
from .models import DiaryEntry


class DiaryEntryForm(forms.ModelForm):
    class Meta:
        model = DiaryEntry
        fields = ["academic_year", "date", "school_class", "section", "subject",
                  "topic", "lecture_summary", "homework", "important_instructions", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "lecture_summary": forms.Textarea(attrs={"rows": 3}),
            "homework": forms.Textarea(attrs={"rows": 2}),
            "important_instructions": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
