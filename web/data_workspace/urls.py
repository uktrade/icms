from django.urls import include, path

from . import views

app_name = "data-workspace"

# To add a new version number, see DataWorkspaceVersionConverter in web/converters.py

urlpatterns = [
    path("table-metadata/", views.MetadataView.as_view(), name="metadata"),
    path(
        "<dwversion:version>/",
        include(
            [
                # User urls
                path("exporters/", views.ExporterDataView.as_view(), name="exporter-data"),
                path("importers/", views.ImporterDataView.as_view(), name="importer-data"),
                path("offices/", views.OfficeDataView.as_view(), name="office-data"),
                path("users/", views.UserDataView.as_view(), name="user-data"),
                path(
                    "user-surveys/",
                    views.UserFeedbackSurveyDataView.as_view(),
                    name="user-survey-data",
                ),
                # Case urls
                # Export application urls
                path(
                    "export-applications/",
                    views.ExportApplicationDataView.as_view(),
                    name="export-application-data",
                ),
                path(
                    "export-certificate-documents/",
                    views.ExportCertificateDocumentDataView.as_view(),
                    name="export-certificate-document-data",
                ),
                path(
                    "com-applications/",
                    views.COMApplicationDataView.as_view(),
                    name="com-application-data",
                ),
                path(
                    "gmp-applications/",
                    views.GMPApplicationDataView.as_view(),
                    name="gmp-application-data",
                ),
                path(
                    "cfs-schedules/",
                    views.CFSScheduleDataView.as_view(),
                    name="cfs-schedule-data",
                ),
                path(
                    "cfs-products/",
                    views.CFSProductDataView.as_view(),
                    name="cfs-product-data",
                ),
                path(
                    "legislations/",
                    views.LegislationDataView.as_view(),
                    name="legislation-data",
                ),
                # Import application urls
                path(
                    "import-applications/",
                    views.ImportApplicationDataView.as_view(),
                    name="import-application-data",
                ),
                path(
                    "import-licence-documents/",
                    views.ImportLicenceDocumentDataView.as_view(),
                    name="import-licence-document-data",
                ),
            ]
        ),
    ),
]
