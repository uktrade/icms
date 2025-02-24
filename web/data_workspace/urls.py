from django.urls import path

from . import views

app_name = "data-workspace"

# To add a new version number, see DataWorkspaceVersionConverter in web/converters.py

urlpatterns = [
    path("<dwversion:version>/users/", views.UserDataView.as_view(), name="user-data"),
]
