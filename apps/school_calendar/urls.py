from django.urls import path
from . import views

app_name = "school_calendar"

urlpatterns = [
    path("", views.CalendarEventListView.as_view(), name="event_list"),
    path("new/", views.CalendarEventCreateView.as_view(), name="event_create"),
]
