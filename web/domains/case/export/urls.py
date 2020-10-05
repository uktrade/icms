from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    path("create", views.ExportApplicationCreateView.as_view(), name="create"),
    path("com/<int:pk>/edit/", views.edit_com, name="com-edit"),
    path("com/<int:pk>/submit/", views.submit_com, name="com-submit"),
    path("case/<int:pk>/take_ownership/", views.take_ownership, name="case-take-ownership"),
    path(
        "case/<int:pk>/release_ownership/", views.release_ownership, name="case-release-ownership",
    ),
    path("case/<int:pk>/management/", views.management, name="case-management"),
    path("case/<int:pk>/management/notes/", views.management_notes, name="case-notes"),
    path("case/<int:pk>/management/notes/add/", views.add_notes, name="case-notes-add"),
    path(
        "case/<int:pk>/management/notes/<int:note_pk>/edit/",
        views.edit_notes,
        name="case-notes-edit",
    ),
    path(
        "case/<int:pk>/management/notes/<int:note_pk>/archive/",
        views.archive_note,
        name="case-notes-archive",
    ),
    path(
        "case/<int:pk>/management/notes/<int:note_pk>/unarchive/",
        views.unarchive_note,
        name="case-notes-unarchive",
    ),
    path(
        "case/<int:pk>/management/notes/<int:note_pk>/files/<int:file_pk>",
        views.archive_file,
        name="case-notes-files-archive",
    ),
    # TODO: add certificate of free sale URLs
]
