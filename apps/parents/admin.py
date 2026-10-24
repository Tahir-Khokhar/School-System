from django.contrib import admin
from .models import Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "relation", "phone", "cnic", "occupation")
    list_filter = ("relation",)
    search_fields = ("full_name", "cnic", "phone", "email")
