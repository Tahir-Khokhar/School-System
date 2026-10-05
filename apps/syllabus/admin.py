from django.contrib import admin
from .models import Syllabus, SyllabusTopic, LecturePlan


class SyllabusTopicInline(admin.TabularInline):
    model = SyllabusTopic
    extra = 1


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "school_class", "subject", "term")
    list_filter = ("term", "academic_year")
    search_fields = ("school_class__name", "subject__name")
    autocomplete_fields = ["academic_year", "school_class", "subject"]
    inlines = [SyllabusTopicInline]


@admin.register(LecturePlan)
class LecturePlanAdmin(admin.ModelAdmin):
    list_display = ("school_class", "subject", "topic", "date", "status")
    list_filter = ("status", "date", "school_class")
    search_fields = ("topic", "lecture_content")
    date_hierarchy = "date"
    autocomplete_fields = ["academic_year", "school_class", "subject", "teacher"]
