from django.urls import include, path

from web.ecil.views import views_export_application as views

app_name = "export-application"
urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path(
                    "export-countries/",
                    views.ExportApplicationExportCountriesUpdateView.as_view(),
                    name="countries",
                ),
                path(
                    "export-countries/<int:country_pk>/remove/",
                    views.ExportApplicationConfirmRemoveCountryFormView.as_view(),
                    name="countries-remove",
                ),
            ]
        ),
    ),
    path(
        "another-contact/",
        views.AnotherExportApplicationContactTemplateView.as_view(),
        name="another-contact",
    ),
]
