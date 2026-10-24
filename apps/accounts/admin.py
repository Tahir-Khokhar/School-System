from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    fieldsets = UserAdmin.fieldsets + (
        ("School", {"fields": ("role", "phone", "avatar", "force_password_change")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("School", {"fields": ("role", "phone")}),
    )
