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
    # TODO: Refactor / group urls
    path("cfs/<int:application_pk>/edit/", views.edit_cfs, name="cfs-edit"),
    path("cfs/<int:application_pk>/schedule/add", views.cfs_add_schedule, name="cfs-schedule-add"),
    path(
        "cfs/<int:application_pk>/schedule/<int:schedule_pk>/edit",
        views.cfs_edit_schedule,
        name="cfs-schedule-edit",
    ),
    path(
        "cfs/<int:application_pk>/schedule/<int:schedule_pk>/delete",
        views.cfs_delete_schedule,
        name="cfs-schedule-delete",
    ),
    path("cfs/<int:application_pk>/submit/", views.submit_cfs, name="cfs-submit"),
]
