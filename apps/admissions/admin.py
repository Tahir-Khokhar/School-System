from django.contrib import admin
from .models import Admission, AdmissionDocument


class AdmissionDocumentInline(admin.TabularInline):
    model = AdmissionDocument
    extra = 1


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("application_no", "full_name", "father_name", "applying_class",
                    "academic_year", "status", "admission_date")
    list_filter = ("status", "academic_year", "applying_class", "gender")
    search_fields = ("application_no", "full_name", "father_name", "parent_name", "parent_cnic")
    autocomplete_fields = ["applying_class", "applying_section", "academic_year", "student", "admission_challan"]
    date_hierarchy = "admission_date"
    readonly_fields = ("application_no", "created_at", "updated_at")
    inlines = [AdmissionDocumentInline]


@admin.register(AdmissionDocument)
class AdmissionDocumentAdmin(admin.ModelAdmin):
    list_display = ("admission", "name", "uploaded_by", "created_at")
    search_fields = ("admission__application_no", "name")
