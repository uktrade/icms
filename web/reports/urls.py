from django.urls import path

from .views import (
    DeleteReportView,
    DownloadReportView,
    ReportListView,
    RunHistoryListView,
    RunOutputView,
    RunReportView,
)

app_name = "report"

urlpatterns = [
    path("", ReportListView.as_view(), name="report-list-view"),
    path("<int:report_pk>/", RunHistoryListView.as_view(), name="run-history-view"),
    path(
        "<int:report_pk>/schedule/<int:schedule_pk>/",
        RunOutputView.as_view(),
        name="run-output-view",
    ),
    path(
        "<int:report_pk>/schedule/<int:schedule_pk>/delete/",
        DeleteReportView.as_view(),
        name="delete-report-view",
    ),
    path(
        "<int:report_pk>/download/<int:pk>/",
        DownloadReportView.as_view(),
        name="download-report-view",
    ),
    path("<int:report_pk>/run/", RunReportView.as_view(), name="run-report-view"),
]
