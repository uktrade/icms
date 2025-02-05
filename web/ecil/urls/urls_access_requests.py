from django.urls import include, path

from web.ecil.views import views_access_requests as views

app_name = "access_request"
urlpatterns = [
    path(
        "new/",
        include(
            [
                path(
                    "step/<str:step>/",
                    views.ExporterAccessRequestMultiStepFormView.as_view(),
                    name="exporter_step_form",
                ),
                path(
                    "remove-export-country/<int:country_pk>/",
                    views.ExporterAccessRequestConfirmRemoveCountryFormView.as_view(),
                    name="remove_export_country_form",
                ),
                # path(
                #     "summary/",
                #     views.ExporterAccessRequestMultiStepFormSummaryView.as_view(),
                #     name="exporter_step_form_summary",
                # ),
            ]
        ),
    ),
]
