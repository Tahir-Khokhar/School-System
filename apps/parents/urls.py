from django.urls import path
from . import views

app_name = "parents"

urlpatterns = [
    path("", views.ParentListView.as_view(), name="parent_list"),
    path("new/", views.ParentCreateView.as_view(), name="parent_create"),
    path("<int:pk>/", views.ParentDetailView.as_view(), name="parent_detail"),
    path("<int:pk>/edit/", views.ParentUpdateView.as_view(), name="parent_edit"),
]
