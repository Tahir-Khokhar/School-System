from django.contrib import admin
from .models import Activity, StudentActivity, Award, Certificate


class StudentActivityInline(admin.TabularInline):
    model = StudentActivity
    extra = 1
    autocomplete_fields = ["student"]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "academic_year")
    list_filter = ("category", "academic_year", "date")
    search_fields = ("title", "description", "location")
    date_hierarchy = "date"
    autocomplete_fields = ["academic_year", "teacher_incharge"]
    filter_horizontal = ("classes",)
    inlines = [StudentActivityInline]


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "date", "certificate_no")
    search_fields = ("student__full_name", "title")
    autocomplete_fields = ["student"]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "issued_date", "certificate_no")
    search_fields = ("student__full_name", "title")
    autocomplete_fields = ["student"]
