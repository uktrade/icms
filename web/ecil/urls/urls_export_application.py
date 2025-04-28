from django.urls import include, path

from web.ecil.views import views_export_application as views

app_name = "export-application"
urlpatterns = [
    #
    # URLs relating to creating an export application
    path(
        "create/",
        include(
            [
                path("", views.CreateExportApplicationStartTemplateView.as_view(), name="new"),
                path(
                    "application-type/",
                    views.CreateExportApplicationAppTypeFormView.as_view(),
                    name="application-type",
                ),
                path(
                    "exporter/",
                    views.CreateExportApplicationExporterFormView.as_view(),
                    name="exporter",
                ),
                path(
                    "exporter-office/",
                    views.CreateExportApplicationExporterOfficeFormView.as_view(),
                    name="exporter-office",
                ),
                path(
                    "export-office/add/",
                    views.CreateExportApplicationExporterOfficeCreateView.as_view(),
                    name="exporter-office-add",
                ),
                path(
                    "exporter-agent/",
                    views.CreateExportApplicationExporterAgentFormView.as_view(),
                    name="exporter-agent",
                ),
                path(
                    "exporter-agent-office/",
                    views.CreateExportApplicationExporterAgentOfficeFormView.as_view(),
                    name="exporter-agent-office",
                ),
                path(
                    "export-agent-office/add/",
                    views.CreateExportApplicationExporterAgentOfficeCreateView.as_view(),
                    name="exporter-agent-office-add",
                ),
                path(
                    "summary/",
                    views.CreateExportApplicationSummaryUpdateView.as_view(),
                    name="summary",
                ),
            ]
        ),
    ),
    path(
        "another-exporter/",
        views.CreateExportApplicationAnotherExporterTemplateView.as_view(),
        name="another-exporter",
    ),
    path(
        "another-exporter-office/",
        views.CreateExportApplicationAnotherExporterOfficeTemplateView.as_view(),
        name="another-exporter-office",
    ),
    path(
        "another-contact/",
        views.CreateExportApplicationAnotherContactTemplateView.as_view(),
        name="another-contact",
    ),
    #
    # URLs relating to editing an in progress export application
    path(
        "edit/<int:application_pk>/",
        include(
            [
                path(
                    "export-countries/",
                    views.ExportApplicationAddExportCountryUpdateView.as_view(),
                    name="countries",
                ),
                path(
                    "export-countries/add-another/",
                    views.ExportApplicationAddAnotherExportCountryFormView.as_view(),
                    name="countries-add-another",
                ),
                path(
                    "export-countries/<int:country_pk>/remove/",
                    views.ExportApplicationConfirmRemoveCountryFormView.as_view(),
                    name="countries-remove",
                ),
            ]
        ),
    ),
]
