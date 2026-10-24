from django import forms
from .models import Activity


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["academic_year", "title", "category", "date", "description",
                  "classes", "location", "result"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
