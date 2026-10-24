from django.contrib import admin
from .models import Teacher, TeacherBankInfo


class TeacherBankInfoInline(admin.StackedInline):
    model = TeacherBankInfo
    extra = 0


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "designation", "status", "joining_date")
    list_filter = ("status", "gender")
    search_fields = ("employee_id", "full_name", "cnic", "email")
    filter_horizontal = ("classes", "sections", "subjects")
    date_hierarchy = "joining_date"
    inlines = [TeacherBankInfoInline]
    readonly_fields = ("employee_id",)


@admin.register(TeacherBankInfo)
class TeacherBankInfoAdmin(admin.ModelAdmin):
    list_display = ("teacher", "bank_name", "account_title", "iban")
    search_fields = ("teacher__full_name", "bank_name", "account_number", "iban")
