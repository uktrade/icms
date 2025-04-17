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
]
