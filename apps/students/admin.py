from django.contrib import admin
from .models import Student, StudentEnrollment


class StudentEnrollmentInline(admin.TabularInline):
    model = StudentEnrollment
    extra = 0
    autocomplete_fields = ["academic_year", "school_class", "section"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("registration_no", "full_name", "father_name", "current_class",
                    "current_section", "status", "admission_date")
    list_filter = ("status", "gender", "current_class")
    search_fields = ("registration_no", "full_name", "father_name", "cnic_or_bform")
    autocomplete_fields = ["parent", "current_class", "current_section"]
    date_hierarchy = "admission_date"
    inlines = [StudentEnrollmentInline]
    readonly_fields = ("registration_no",)


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "academic_year", "school_class", "section", "roll_no", "promotion_status")
    list_filter = ("academic_year", "school_class", "promotion_status")
    search_fields = ("student__full_name", "student__registration_no", "roll_no")
    autocomplete_fields = ["student", "academic_year", "school_class", "section"]
