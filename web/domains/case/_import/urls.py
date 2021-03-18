from django.urls import include, path

from . import views

app_name = "import"

urlpatterns = [
    path("", views.ImportApplicationChoiceView.as_view(), name="choice"),
    path("create/sanctions/", views.create_sanctions, name="create-sanctions"),
    path("create/firearms/oil/", views.create_oil, name="create-oil"),
    path("create/wood/quota/", views.create_wood_quota, name="create-wood-quota"),
    # Applications
    path("sanctions/", include("web.domains.case._import.sanctions.urls")),
    path("firearms/", include("web.domains.case._import.firearms.urls")),
    path("wood/", include("web.domains.case._import.wood.urls")),
    # Importer case management
    path("case/<int:pk>/withdraw/", views.withdraw_case, name="withdraw-case"),
    path(
        "case/<int:application_pk>/withdraw/<int:withdrawal_pk>/archive/",
        views.archive_withdrawal,
        name="archive-withdrawal",
    ),
    path(
        "case/<int:application_pk>/firs/list/",
        views.list_firs,
        name="list-firs",
    ),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/respond/",
        views.respond_fir,
        name="respond-fir",
    ),
    # ILB Admin Case management
    path(
        "case/<int:pk>/take_ownership/",
        views.take_ownership,
        name="take-ownership",
    ),
    path(
        "case/<int:pk>/release_ownership/",
        views.release_ownership,
        name="release-ownership",
    ),
    path("case/<int:pk>/management/", views.manage_case, name="case-management"),
    path("case/<int:pk>/withdrawals", views.manage_withdrawals, name="manage-withdrawals"),
    path(
        "case/<int:pk>/update-requests/",
        views.manage_update_requests,
        name="manage-update-requests",
    ),
    path(
        "case/<int:application_pk>/update-requests/<int:update_request_pk>/close/",
        views.close_update_requests,
        name="close-update-requests",
    ),
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
        "case/<int:application_pk>/management/notes/<int:note_pk>/files/<int:file_pk>",
        views.archive_note_file,
        name="archive-note-file",
    ),
    path("case/<int:application_pk>/firs/manage/", views.manage_firs, name="manage-firs"),
    path("case/<int:application_pk>/firs/add/", views.add_fir, name="add-fir"),
    path("case/<int:application_pk>/firs/<int:fir_pk>/edit/", views.edit_fir, name="edit-fir"),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/archive/",
        views.archive_fir,
        name="archive-fir",
    ),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/withdraw/",
        views.withdraw_fir,
        name="withdraw-fir",
    ),
    path("case/<int:application_pk>/firs/<int:fir_pk>/close/", views.close_fir, name="close-fir"),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk/files/<int:file_pk/archive/",
        views.archive_fir_file,
        name="archive-fir-file",
    ),
    path("case/<int:pk>/prepare-response/", views.prepare_response, name="prepare-response"),
    path(
        "case/<int:pk>/cover-letter/",
        views.edit_cover_letter,
        name="edit-cover-letter",
    ),
    path(
        "case/<int:pk>/licence/",
        views.edit_licence,
        name="edit-licence",
    ),
    path(
        "case/<int:pk>/endorsements/add/",
        views.add_endorsement,
        name="add-endorsement",
    ),
    path(
        "case/<int:pk>/endorsements/add-custom/",
        views.add_custom_endorsement,
        name="add-custom-endorsement",
    ),
    path(
        "case/<int:application_pk>/endorsements/<int:endorsement_pk>/edit/",
        views.edit_endorsement,
        name="edit-endorsement",
    ),
    path(
        "case/<int:application_pk>/endorsements/<int:endorsement_pk>/delete/",
        views.delete_endorsement,
        name="delete-endorsement",
    ),
    path(
        "case/<int:pk>/cover-letter/preview/",
        views.preview_cover_letter,
        name="preview-cover-letter",
    ),
    path(
        "case/<int:pk>/licence/preview/",
        views.preview_licence,
        name="preview-licence",
    ),
    # Common to Importer/ILB Admin
    path("case/<int:pk>/view/", views.view_case, name="view-case"),
]
