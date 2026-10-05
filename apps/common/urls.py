"""Common app URL routing — academic years, classes, subjects, global search."""
from django.urls import path
from . import views

app_name = "common"

urlpatterns = [
    path("academic-years/", views.AcademicYearListView.as_view(), name="academic_year_list"),
    path("academic-years/new/", views.AcademicYearCreateView.as_view(), name="academic_year_create"),
    path("academic-years/<int:pk>/activate/", views.AcademicYearActivateView.as_view(), name="academic_year_activate"),
    path("academic-years/<int:pk>/", views.AcademicYearDetailView.as_view(), name="academic_year_detail"),
    path("classes/", views.ClassListView.as_view(), name="class_list"),
    path("classes/new/", views.ClassCreateView.as_view(), name="class_create"),
    path("subjects/", views.SubjectListView.as_view(), name="subject_list"),
    path("subjects/new/", views.SubjectCreateView.as_view(), name="subject_create"),
    path("search/", views.GlobalSearchView.as_view(), name="global_search"),
]
