from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "start_date", "end_date", "location", "is_public")
    list_filter = ("category", "is_public", "academic_year")
    search_fields = ("title", "description", "location")
    date_hierarchy = "start_date"
