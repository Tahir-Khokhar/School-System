from django import forms
from .models import Homework, HomeworkSubmission


ALLOWED_FILE_TYPES = [".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".zip"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


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

    def clean_attachment(self):
        """Validate the teacher-uploaded learning resource."""
        attachment = self.cleaned_data.get("attachment")
        if attachment:
            import os
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext not in ALLOWED_FILE_TYPES:
                raise forms.ValidationError(
                    f"File type '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
                )
            if attachment.size > MAX_FILE_SIZE:
                raise forms.ValidationError(
                    f"File size ({attachment.size // 1024}KB) exceeds maximum (10MB)."
                )
        return attachment

    def clean(self):
        cleaned_data = super().clean()
        assigned = cleaned_data.get("assigned_date")
        due = cleaned_data.get("due_date")
        if assigned and due and due < assigned:
            raise forms.ValidationError(
                "Due date cannot be earlier than the assigned date."
            )
        return cleaned_data


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ["text", "file", "marks", "feedback"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3}), "feedback": forms.Textarea(attrs={"rows": 2})}

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Validate file extension
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_FILE_TYPES:
                raise forms.ValidationError(
                    f"File type '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
                )
            # Validate file size
            if file.size > MAX_FILE_SIZE:
                raise forms.ValidationError(
                    f"File size ({file.size // 1024}KB) exceeds maximum (10MB)."
                )
        return file
