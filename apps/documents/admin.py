from django.contrib import admin
from .models import StudentDocument, StudentIDCard


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ("student", "name", "uploaded_by", "created_at")
    search_fields = ("student__full_name", "name")
    autocomplete_fields = ["student", "uploaded_by"]


@admin.register(StudentIDCard)
class StudentIDCardAdmin(admin.ModelAdmin):
    list_display = ("student", "card_no", "issued_date", "valid_until")
    search_fields = ("student__full_name", "card_no")
    autocomplete_fields = ["student"]
