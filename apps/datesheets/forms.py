from django import forms
from .models import DateSheet, DateSheetItem


class DateSheetForm(forms.ModelForm):
    class Meta:
        model = DateSheet
        fields = ["academic_year", "title", "term", "school_class", "status"]


class DateSheetItemForm(forms.ModelForm):
    class Meta:
        model = DateSheetItem
        fields = ["subject", "date", "start_time", "end_time", "room", "instructions"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError(
                "End time must be later than the start time."
            )
        return cleaned
