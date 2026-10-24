from django.contrib import admin
from .models import DateSheet, DateSheetItem


class DateSheetItemInline(admin.TabularInline):
    model = DateSheetItem
    extra = 1
    autocomplete_fields = ["subject"]


@admin.register(DateSheet)
class DateSheetAdmin(admin.ModelAdmin):
    list_display = ("title", "academic_year", "school_class", "term", "status", "published_at")
    list_filter = ("status", "term", "academic_year")
    search_fields = ("title",)
    autocomplete_fields = ["academic_year", "school_class", "published_by"]
    inlines = [DateSheetItemInline]
