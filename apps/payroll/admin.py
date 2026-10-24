from django.contrib import admin
from .models import Payroll, SalaryPayment


class SalaryPaymentInline(admin.StackedInline):
    model = SalaryPayment
    extra = 0
    readonly_fields = ("amount", "payment_date", "method", "transaction_ref", "is_successful", "recorded_by")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("teacher", "month", "basic_salary", "allowances", "deductions",
                    "net_salary", "status")
    list_filter = ("status", "month")
    search_fields = ("teacher__full_name", "teacher__employee_id", "month")
    autocomplete_fields = ["teacher", "approved_by"]
    inlines = [SalaryPaymentInline]
