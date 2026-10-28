from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("", views.StudentDocumentListView.as_view(), name="list"),
    path("new/", views.StudentDocumentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StudentDocumentDetailView.as_view(), name="detail"),
    path("<int:pk>/download/", views.StudentDocumentDownloadView.as_view(), name="download"),
    path("<int:pk>/delete/", views.StudentDocumentDeleteView.as_view(), name="delete"),
]
