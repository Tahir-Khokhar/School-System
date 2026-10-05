from django.contrib import admin
from .models import (
    ClassTest, TestResult, SurpriseTest, SurpriseTestResult,
    Exam, ExamSubject, ExamResult, TermResult,
)


class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 1
    autocomplete_fields = ["student"]


@admin.register(ClassTest)
class ClassTestAdmin(admin.ModelAdmin):
    list_display = ("title", "school_class", "subject", "date", "total_marks", "passing_marks", "status")
    list_filter = ("status", "school_class", "academic_year")
    search_fields = ("title", "topics")
    date_hierarchy = "date"
    autocomplete_fields = ["academic_year", "school_class", "section", "subject"]
    inlines = [TestResultInline]


@admin.register(SurpriseTest)
class SurpriseTestAdmin(admin.ModelAdmin):
    list_display = ("title", "school_class", "subject", "date", "total_marks", "status")
    list_filter = ("status", "school_class", "academic_year")
    search_fields = ("title",)
    date_hierarchy = "date"
    autocomplete_fields = ["academic_year", "school_class", "subject"]


class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "term", "academic_year", "start_date", "end_date", "is_published")
    list_filter = ("term", "academic_year", "is_published")
    search_fields = ("name",)
    date_hierarchy = "start_date"
    autocomplete_fields = ["academic_year"]
    inlines = [ExamSubjectInline]


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = ("student", "academic_year", "term", "percentage", "grade", "rank", "status")
    list_filter = ("status", "term", "academic_year")
    search_fields = ("student__full_name", "student__registration_no")
    autocomplete_fields = ["student", "academic_year"]
