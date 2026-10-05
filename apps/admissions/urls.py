from django.urls import path
from . import views

app_name = "admissions"

urlpatterns = [
    path("", views.AdmissionApplicationListView.as_view(), name="application_list"),
    path("new/", views.AdmissionApplicationCreateView.as_view(), name="application_create"),
    path("<int:pk>/", views.AdmissionApplicationDetailView.as_view(), name="application_detail"),
    path("<int:pk>/edit/", views.AdmissionApplicationUpdateView.as_view(), name="application_edit"),
    path("<int:pk>/submit/", views.AdmissionSubmitView.as_view(), name="application_submit"),
    path("<int:pk>/verify/", views.AdmissionVerifyView.as_view(), name="application_verify"),
    path("<int:pk>/approve/", views.AdmissionApproveView.as_view(), name="application_approve"),
    path("<int:pk>/reject/", views.AdmissionRejectView.as_view(), name="application_reject"),
    path("<int:pk>/register/", views.AdmissionRegisterStudentView.as_view(), name="application_register"),
    path("<int:pk>/generate-challan/", views.AdmissionGenerateChallanView.as_view(), name="application_generate_challan"),
]
