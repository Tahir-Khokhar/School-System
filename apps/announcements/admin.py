from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "publish_date", "expiry_date", "is_published", "author")
    list_filter = ("audience", "is_published", "academic_year")
    search_fields = ("title", "description")
    date_hierarchy = "publish_date"
    autocomplete_fields = ["academic_year", "target_class", "target_section", "author"]
