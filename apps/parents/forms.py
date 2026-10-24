from django import forms
from .models import Parent


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ["full_name", "relation", "cnic", "phone", "email",
                  "occupation", "address", "annual_income"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}
