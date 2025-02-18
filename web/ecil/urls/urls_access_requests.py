from django.urls import include, path

from web.ecil.views import views_access_requests as views

app_name = "access_request"
urlpatterns = [
    path(
        "new/",
        include(
            [
                path(
                    "exporter-or-agent/",
                    views.ExporterAccessRequestTypeFormView.as_view(),
                    name="new",
                ),
                path(
                    "step/<str:step>/",
                    views.ExporterAccessRequestMultiStepFormView.as_view(),
                    name="exporter_step_form",
                ),
                path(
                    "agent-step/<str:step>/",
                    views.ExporterAccessRequestAgentMultiStepFormView.as_view(),
                    name="exporter_agent_step_form",
                ),
                path(
                    "remove-export-country/<int:country_pk>/",
                    views.ExporterAccessRequestConfirmRemoveCountryFormView.as_view(),
                    name="remove_export_country_form",
                ),
                path(
                    "summary/",
                    views.ExporterAccessRequestMultiStepFormSummaryView.as_view(),
                    name="exporter_step_form_summary",
                ),
                path(
                    "agent-summary/",
                    views.ExporterAccessRequestAgentMultiStepFormSummaryView.as_view(),
                    name="exporter_agent_step_form_summary",
                ),
            ]
        ),
    ),
    path(
        "<int:access_request_pk>/",
        include(
            [
                path(
                    "submitted/",
                    views.AccessRequestSubmittedDetailView.as_view(),
                    name="submitted_detail",
                ),
            ]
        ),
    ),
]
