from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["academic_year", "title", "description", "audience",
                  "target_class", "target_section", "attachment",
                  "publish_date", "expiry_date", "is_published"]
        widgets = {
            "publish_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expiry_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
