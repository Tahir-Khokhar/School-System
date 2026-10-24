from django.contrib import admin
from .models import DiaryEntry


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "school_class", "section", "subject", "topic", "teacher")
    list_filter = ("date", "school_class", "academic_year")
    search_fields = ("topic", "lecture_summary", "homework")
    date_hierarchy = "date"
    autocomplete_fields = ["academic_year", "school_class", "section", "subject", "teacher"]
