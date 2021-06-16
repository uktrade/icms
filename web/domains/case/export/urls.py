from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    # List export applications
    path("", views.ExportApplicationChoiceView.as_view(), name="choose"),
    # Create all export applications
    path(
        "create/<exportapplicationtype:type_code>/",
        views.create_export_application,
        name="create-application",
    ),
    # Certificate of manufacture application urls
    path("com/<int:application_pk>/edit/", views.edit_com, name="com-edit"),
    path("com/<int:pk>/submit/", views.submit_com, name="com-submit"),
    # TODO: add certificate of free sale URLs
]
