from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    path("", views.TeacherListView.as_view(), name="teacher_list"),
    path("new/", views.TeacherCreateView.as_view(), name="teacher_create"),
    path("<int:pk>/", views.TeacherDetailView.as_view(), name="teacher_detail"),
    path("<int:pk>/edit/", views.TeacherUpdateView.as_view(), name="teacher_edit"),
    path("<int:pk>/bank-info/", views.TeacherBankInfoView.as_view(), name="teacher_bank_info"),
]
