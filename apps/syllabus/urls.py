from django.urls import path
from . import views

app_name = "syllabus"

urlpatterns = [
    path("", views.SyllabusListView.as_view(), name="syllabus_list"),
    path("new/", views.SyllabusCreateView.as_view(), name="syllabus_create"),
    path("<int:pk>/", views.SyllabusDetailView.as_view(), name="syllabus_detail"),
    path("<int:pk>/topic/", views.SyllabusTopicCreateView.as_view(), name="topic_create"),
    path("topic/<int:pk>/", views.SyllabusTopicUpdateView.as_view(), name="topic_edit"),
    path("lectures/", views.LecturePlanListView.as_view(), name="lecture_list"),
    path("lectures/new/", views.LecturePlanCreateView.as_view(), name="lecture_create"),
]
