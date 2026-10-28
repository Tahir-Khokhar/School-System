"""Forms for the documents app."""
from django import forms
from .models import StudentDocument


class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ["student", "name", "file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Extension + size validation lives in the model field's
            # validators= list, but we double-check here so the form
            # surfaces a user-friendly error message rather than letting
            # the model save() raise IntegrityError.
            import os
            from apps.common.validators import (
                ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES,
            )
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise forms.ValidationError(
                    f"File type '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
                )
            if file.size > MAX_FILE_SIZE_BYTES:
                raise forms.ValidationError(
                    f"File size ({file.size // 1024}KB) exceeds maximum (10MB)."
                )
        return file
