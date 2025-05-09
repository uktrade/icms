from django.urls import path

from . import views

app_name = "data-workspace"

# To add a new version number, see DataWorkspaceVersionConverter in web/converters.py

urlpatterns = [
    path("table-metadata/", views.MetadataView.as_view(), name="metadata"),
    path("<dwversion:version>/exporters/", views.ExporterDataView.as_view(), name="exporter-data"),
    path("<dwversion:version>/importers/", views.ImporterDataView.as_view(), name="importer-data"),
    path("<dwversion:version>/offices/", views.OfficeDataView.as_view(), name="office-data"),
    path("<dwversion:version>/users/", views.UserDataView.as_view(), name="user-data"),
    path(
        "<dwversion:version>/user-surveys/",
        views.UserFeedbackSurveyDataView.as_view(),
        name="user-survey-data",
    ),
    path(
        "<dwversion:version>/case-documents/",
        views.CaseDocumentDataView.as_view(),
        name="case-document-data",
    ),
    path(
        "<dwversion:version>/export-applications/",
        views.ExportApplicationDataView.as_view(),
        name="export-application-data",
    ),
    path(
        "<dwversion:version>/com-applications/",
        views.COMApplicationDataView.as_view(),
        name="com-application-data",
    ),
    path(
        "<dwversion:version>/gmp-applications/",
        views.GMPApplicationDataView.as_view(),
        name="gmp-application-data",
    ),
    path(
        "<dwversion:version>/cfs-schedules/",
        views.CFSScheduleDataView.as_view(),
        name="cfs-schedule-data",
    ),
    path(
        "<dwversion:version>/cfs-products/",
        views.CFSProductDataView.as_view(),
        name="cfs-product-data",
    ),
    path(
        "<dwversion:version>/legislations/",
        views.LegislationDataView.as_view(),
        name="legislation-data",
    ),
]
