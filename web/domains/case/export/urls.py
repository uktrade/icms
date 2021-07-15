from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    # List export applications
    path("", views.ExportApplicationChoiceView.as_view(), name="choose"),
    # common create
    path(
        "create/<exportapplicationtype:type_code>/",
        views.create_export_application,
        name="create-application",
    ),
    # Certificate of manufacture
    path("com/<int:application_pk>/edit/", views.edit_com, name="com-edit"),
    path("com/<int:application_pk>/submit/", views.submit_com, name="com-submit"),
    # Certificate of free sale
    path("cfs/<int:application_pk>/edit/", views.edit_cfs, name="cfs-edit"),
    # path("cfs/<int:application_pk>/submit/", views.submit_cfs, name="cfs-submit"),
]
