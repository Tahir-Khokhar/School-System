from django.contrib import admin
from .models import Homework, HomeworkSubmission


class HomeworkSubmissionInline(admin.TabularInline):
    model = HomeworkSubmission
    extra = 0
    autocomplete_fields = ["student"]


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ("title", "school_class", "subject", "assigned_date", "due_date", "status")
    list_filter = ("status", "school_class", "academic_year")
    search_fields = ("title", "description")
    date_hierarchy = "assigned_date"
    autocomplete_fields = ["academic_year", "school_class", "section", "subject", "teacher"]
    inlines = [HomeworkSubmissionInline]


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("homework", "student", "submitted_at", "marks", "is_reviewed")
    search_fields = ("homework__title", "student__full_name")
    autocomplete_fields = ["homework", "student"]
