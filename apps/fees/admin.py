from django.contrib import admin
from .models import (
    FeeType, FeeStructure, FeeChallan, FeeChallanItem, FeePayment,
)


class FeeChallanItemInline(admin.TabularInline):
    model = FeeChallanItem
    extra = 1
    autocomplete_fields = ["fee_type"]


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ("receipt_no", "amount", "method", "payment_date", "recorded_by", "is_successful")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "fee_type", "default_amount", "is_active")
    list_filter = ("fee_type", "is_active")
    search_fields = ("name", "code")


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "school_class", "fee_type", "amount", "applies_monthly", "is_active")
    list_filter = ("academic_year", "applies_monthly", "is_active")
    autocomplete_fields = ["academic_year", "school_class", "fee_type"]


@admin.register(FeeChallan)
class FeeChallanAdmin(admin.ModelAdmin):
    list_display = ("challan_no", "student", "academic_year", "month",
                    "total_payable", "total_paid", "status", "issue_date", "due_date")
    list_filter = ("status", "is_admission_challan", "academic_year", "month")
    search_fields = ("challan_no", "student__full_name", "student__registration_no", "month")
    autocomplete_fields = ["student", "academic_year"]
    date_hierarchy = "issue_date"
    readonly_fields = ("challan_no", "created_at", "updated_at")
    inlines = [FeeChallanItemInline, FeePaymentInline]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "challan", "amount", "method", "payment_date", "is_successful", "recorded_by")
    list_filter = ("method", "is_successful")
    search_fields = ("receipt_no", "challan__challan_no", "transaction_ref")
    date_hierarchy = "payment_date"
    readonly_fields = ("receipt_no",)
