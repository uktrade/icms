from django.urls import path

from . import views

app_name = "perm_test"

urlpatterns = [
    path("", views.PermissionTestHarnessView.as_view(), name="harness"),
    path("create-data/", views.CreateHarnessDataView.as_view(), name="create-data"),
]
