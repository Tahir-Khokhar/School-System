from django.urls import path
from . import views

app_name = "activities"

urlpatterns = [
    path("", views.ActivityListView.as_view(), name="activity_list"),
    path("new/", views.ActivityCreateView.as_view(), name="activity_create"),
    path("<int:pk>/", views.ActivityDetailView.as_view(), name="activity_detail"),
]
