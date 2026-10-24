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
