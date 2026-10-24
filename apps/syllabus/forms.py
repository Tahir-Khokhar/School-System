from django import forms
from .models import Syllabus, SyllabusTopic, LecturePlan


class SyllabusForm(forms.ModelForm):
    class Meta:
        model = Syllabus
        fields = ["academic_year", "school_class", "subject", "term", "description"]


class SyllabusTopicForm(forms.ModelForm):
    class Meta:
        model = SyllabusTopic
        fields = ["chapter", "topic", "description", "expected_completion_date",
                  "priority", "status", "notes"]
        widgets = {"expected_completion_date": forms.DateInput(attrs={"type": "date"})}


class LecturePlanForm(forms.ModelForm):
    class Meta:
        model = LecturePlan
        fields = ["academic_year", "school_class", "subject", "topic", "date",
                  "learning_objectives", "lecture_content", "activities",
                  "homework", "resources", "estimated_duration", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
