from django.urls import path
from . import views

app_name = "homework"

urlpatterns = [
    path("", views.HomeworkListView.as_view(), name="homework_list"),
    path("new/", views.HomeworkCreateView.as_view(), name="homework_create"),
    path("<int:pk>/", views.HomeworkDetailView.as_view(), name="homework_detail"),
    path("<int:pk>/edit/", views.HomeworkUpdateView.as_view(), name="homework_edit"),
]
