from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    path("create", views.ExportApplicationCreateView.as_view(), name="create"),
    path("com/<int:pk>/edit/", views.edit_com, name="com-edit"),
    path("com/<int:pk>/submit/", views.submit_com, name="com-submit"),
    path("case/<int:pk>/take_ownership/", views.take_ownership, name="case-take-ownership"),
    path("case/<int:pk>/release_ownership/", views.release_ownership, name="release-ownership"),
    path("case/<int:pk>/management/", views.management, name="case-management"),
    # notes
    path("case/<int:pk>/management/notes/", views.list_notes, name="list-notes"),
    path("case/<int:pk>/management/notes/add/", views.add_note, name="add-note"),
    path(
        "case/<int:application_pk>/management/notes/<int:note_pk>/edit/",
        views.edit_note,
        name="edit-note",
    ),
    path(
        "case/<int:application_pk>/management/notes/<int:note_pk>/archive/",
        views.archive_note,
        name="archive-note",
    ),
    path(
        "case/<int:application_pk>/management/notes/<int:note_pk>/unarchive/",
        views.unarchive_note,
        name="unarchive-note",
    ),
    path(
        "case/<int:application_pk>/notes/<int:note_pk>/add-document/",
        views.add_note_document,
        name="add-note-document",
    ),
    path(
        "case/<int:application_pk>/notes/<int:note_pk>/view-document/<int:file_pk>",
        views.view_note_document,
        name="view-note-document",
    ),
    path(
        "case/<int:application_pk>/management/notes/<int:note_pk>/delete-document/<int:file_pk>",
        views.delete_note_document,
        name="delete-note-document",
    ),
    # TODO: add certificate of free sale URLs
]
