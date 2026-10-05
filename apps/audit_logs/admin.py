from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "object_repr", "object_app", "object_model")
    list_filter = ("action", "object_app", "object_model")
    search_fields = ("object_repr", "description", "user__username")
    date_hierarchy = "timestamp"
    readonly_fields = [f.name for f in AuditLog._meta.fields]
