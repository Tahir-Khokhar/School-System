from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("challans/", views.FeeChallanListView.as_view(), name="challan_list"),
    path("challans/<int:pk>/", views.FeeChallanDetailView.as_view(), name="challan_detail"),
    path("challans/<int:pk>/print/", views.FeeChallanPrintView.as_view(), name="challan_print"),
    path("challans/<int:pk>/pdf/", views.FeeChallanPDFView.as_view(), name="challan_pdf"),
    path("challans/<int:pk>/pay/", views.OnlinePaymentStartView.as_view(), name="online_pay"),
    path("challans/generate/", views.MonthlyChallanGenerateView.as_view(), name="challan_generate"),
    path("payments/", views.FeePaymentListView.as_view(), name="payment_list"),
    path("payment/", views.ChallanLookupView.as_view(), name="payment_create"),
    path("payment/<int:challan_pk>/", views.PaymentConfirmView.as_view(), name="payment_confirm"),
    path("receipts/<int:pk>/pdf/", views.ReceiptPDFView.as_view(), name="receipt_pdf"),
    path("defaulters/", views.FeeDefaulterReportView.as_view(), name="defaulter_report"),
    path("fee-types/", views.FeeTypeListView.as_view(), name="fee_type_list"),
    path("fee-types/new/", views.FeeTypeCreateView.as_view(), name="fee_type_create"),
    path("structures/", views.FeeStructureListView.as_view(), name="structure_list"),
    path("structures/new/", views.FeeStructureCreateView.as_view(), name="structure_create"),
    # Gateway endpoints
    path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),
    path("payment/jazzcash/return/", views.JazzCashReturnView.as_view(), name="gateway_jazzcash_return"),
    path("payment/stripe/return/", views.StripeReturnView.as_view(), name="gateway_stripe_return"),
    path("payment/test/<int:pk>/<str:session_id>/", views.TestGatewayPayView.as_view(), name="gateway_test_pay"),
]
