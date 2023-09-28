from django.urls import path

from . import views

app_name = "harness"

urlpatterns = [
    path("permissions/", views.PermissionTestHarnessView.as_view(), name="permissions"),
    path(
        "permissions/create-data/",
        views.CreateHarnessDataView.as_view(),
        name="create-permission-data",
    ),
    path("localisation/", views.L10NTestHarnessView.as_view(), name="l10n"),  # /PS-IGNORE
]
