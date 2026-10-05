from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("mark/", views.AttendanceMarkView.as_view(), name="daily_mark"),
    path("report/", views.AttendanceReportView.as_view(), name="report"),
]
