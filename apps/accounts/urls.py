from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("security/2fa/", views.Setup2FAView.as_view(), name="setup_2fa"),
    path("security/2fa/verify/", views.Verify2FAView.as_view(), name="verify_2fa"),
    path("security/2fa/disable/", views.Disable2FAView.as_view(), name="disable_2fa"),
]
