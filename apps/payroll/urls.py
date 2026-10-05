from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    path("", views.PayrollListView.as_view(), name="payroll_list"),
    path("new/", views.PayrollCreateView.as_view(), name="payroll_create"),
    path("<int:pk>/", views.PayrollDetailView.as_view(), name="payroll_detail"),
    path("<int:pk>/approve/", views.PayrollApproveView.as_view(), name="payroll_approve"),
    path("<int:pk>/pay/", views.PayrollPayView.as_view(), name="payroll_pay"),
    path("<int:pk>/slip/pdf/", views.SalarySlipPDFView.as_view(), name="salary_slip_pdf"),
]
