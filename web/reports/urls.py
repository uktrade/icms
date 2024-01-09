from django.urls import path

from .views import (
    DownloadReportView,
    ReportListView,
    RunHistoryListView,
    RunOutputView,
    RunReportView,
)

urlpatterns = [
    path("", ReportListView.as_view(), name="report-list-view"),
    path("<int:report_pk>/", RunHistoryListView.as_view(), name="run-history-view"),
    path(
        "<int:report_pk>/schedule/<int:schedule_pk>/",
        RunOutputView.as_view(),
        name="run-output-view",
    ),
    path(
        "<int:report_pk>/download/<int:pk>/",
        DownloadReportView.as_view(),
        name="download-report-view",
    ),
    path("<int:report_pk>/run/", RunReportView.as_view(), name="run-report-view"),
]
