from django.urls import path

from . import views

app_name = "perm_test"

urlpatterns = [
    path("", views.PermissionTestHarness.as_view(), name="harness"),
]
