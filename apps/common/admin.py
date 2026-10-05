from django.contrib import admin
from .models import AcademicYear, School, SchoolClass, Section, Subject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active", "is_archived")
    list_filter = ("is_active", "is_archived")
    search_fields = ("name",)
    date_hierarchy = "start_date"
    ordering = ("-start_date",)


admin.site.register(School)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "grade_level", "order", "is_active")
    list_filter = ("grade_level", "is_active")
    search_fields = ("name",)
    inlines = [SectionInline]
    ordering = ("order", "name")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("school_class", "name", "capacity", "is_active")
    list_filter = ("is_active", "school_class")
    search_fields = ("name", "school_class__name")
    autocomplete_fields = ["school_class"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_compulsory", "is_active")
    list_filter = ("is_compulsory", "is_active")
    search_fields = ("name", "code")
