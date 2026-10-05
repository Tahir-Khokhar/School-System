from django.urls import path
from . import views

app_name = "examinations"

urlpatterns = [
    path("class-tests/", views.ClassTestListView.as_view(), name="classtest_list"),
    path("class-tests/new/", views.ClassTestCreateView.as_view(), name="classtest_create"),
    path("class-tests/<int:pk>/", views.ClassTestDetailView.as_view(), name="classtest_detail"),
    path("class-tests/<int:pk>/results/", views.ClassTestResultsView.as_view(), name="classtest_results"),
    path("surprise-tests/", views.SurpriseTestListView.as_view(), name="surprisetest_list"),
    path("surprise-tests/new/", views.SurpriseTestCreateView.as_view(), name="surprisetest_create"),
    path("exams/", views.ExamListView.as_view(), name="exam_list"),
    path("exams/new/", views.ExamCreateView.as_view(), name="exam_create"),
    path("exams/<int:pk>/", views.ExamDetailView.as_view(), name="exam_detail"),
    path("term-results/", views.TermResultListView.as_view(), name="termresult_list"),
    path("term-results/<int:pk>/publish/", views.TermResultPublishView.as_view(), name="termresult_publish"),
    path("report-card/<int:pk>/pdf/", views.ReportCardPDFView.as_view(), name="report_card_pdf"),
]
