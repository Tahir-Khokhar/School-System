from django.urls import path
from . import views

app_name = "diary"

urlpatterns = [
    path("", views.DiaryEntryListView.as_view(), name="entry_list"),
    path("new/", views.DiaryEntryCreateView.as_view(), name="entry_create"),
    path("<int:pk>/", views.DiaryEntryDetailView.as_view(), name="entry_detail"),
    path("<int:pk>/edit/", views.DiaryEntryUpdateView.as_view(), name="entry_edit"),
]
