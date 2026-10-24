from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "notification_type", "is_read", "sent_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__username", "title", "message")
    date_hierarchy = "sent_at"
