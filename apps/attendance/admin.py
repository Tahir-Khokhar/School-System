from django.contrib import admin
from .models import Attendance, TeacherAttendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "school_class", "section", "subject", "status", "marked_by")
    list_filter = ("status", "school_class", "date", "academic_year")
    search_fields = ("student__full_name", "student__registration_no")
    date_hierarchy = "date"
    autocomplete_fields = ["student", "academic_year", "school_class", "section", "subject", "marked_by"]


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ("teacher", "date", "status", "arrival_time", "departure_time")
    list_filter = ("status", "date")
    search_fields = ("teacher__full_name", "teacher__employee_id")
    date_hierarchy = "date"
    autocomplete_fields = ["teacher", "marked_by"]
