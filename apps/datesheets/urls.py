from django.urls import path
from . import views

app_name = "datesheets"

urlpatterns = [
    path("", views.DateSheetListView.as_view(), name="datesheet_list"),
    path("new/", views.DateSheetCreateView.as_view(), name="datesheet_create"),
    path("<int:pk>/", views.DateSheetDetailView.as_view(), name="datesheet_detail"),
    path("<int:pk>/publish/", views.DateSheetPublishView.as_view(), name="datesheet_publish"),
    path("<int:pk>/items/", views.DateSheetItemCreateView.as_view(), name="item_create"),
]
