from django.urls import include, path

from . import views

app_name = "case"

note_urls = [
    path("list/", views.list_notes, name="list-notes"),
    path("add/", views.add_note, name="add-note"),
    path(
        "<int:note_pk>/",
        include(
            [
                path("edit/", views.edit_note, name="edit-note"),
                path("archive/", views.archive_note, name="archive-note"),
                path("unarchive/", views.unarchive_note, name="unarchive-note"),
                path(
                    "documents/",
                    include(
                        [
                            path("add/", views.add_note_document, name="add-note-document"),
                            path(
                                "<int:file_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views.view_note_document,
                                            name="view-note-document",
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_note_document,
                                            name="delete-note-document",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]

admin_urls = [
    path("manage-withdrawals/", views.manage_withdrawals, name="manage-withdrawals"),
]

applicant_case_management_urls = [
    path("withdraw/", views.withdraw_case, name="withdraw-case"),
    path(
        "withdraw/<int:withdrawal_pk>/archive/", views.archive_withdrawal, name="archive-withdrawal"
    ),
]

urlpatterns = [
    path(
        "<casetype:case_type>/<int:application_pk>/",
        include(
            [
                # --- further information requests (TODO: ICMSLST-665)
                #     NOTE: these are the only ones that take AcceptRequest
                #
                # path("firs/list/", views.list_firs, name="list-firs"),
                # path("firs/", views.manage_firs, name="manage-firs"),
                # path("firs/add/", views.add_fir, name="add-fir"),
                # path("firs/<int:fir_pk>/edit/", views.edit_fir, name="edit-fir"),
                # path("firs/<int:fir_pk>/respond/", views.respond_fir, name="respond-fir"),
                # path("firs/<int:fir_pk>/archive/", views.archive_fir, name="archive-fir"),
                # path("firs/<int:fir_pk>/withdraw/", views.withdraw_fir, name="withdraw-fir"),
                # path("firs/<int:fir_pk>/close/", views.close_fir, name="close-fir"),
                # path(
                #     "firs/<int:fir_pk/files/<int:file_pk/archive/",
                #     views.archive_fir_file,
                #     name="archive-fir-file",
                # ),
                #
                # --- applicant case management
                path("applicant-case-management/", include(applicant_case_management_urls)),
                #
                # -- ILB Admin Case management (TODO: ICMSLST-667)
                #
                path("admin/", include(admin_urls)),
                # path("take_ownership/", views.take_ownership, name="take-ownership"),
                # path("release_ownership/", views.release_ownership, name="release-ownership"),
                # path("management/", views.manage_case, name="case-management"),
                # path(
                #     "update-requests/", views.manage_update_requests, name="manage-update-requests"
                # ),
                # path(
                #     "update-requests/<int:update_request_pk>/close/",
                #     views.close_update_requests,
                #     name="close-update-requests",
                # ),
                #
                # --- notes
                #
                path("notes/", include(note_urls)),
                #
                # --- ??? (TODO: ICMSLST-669)
                #
                # path("prepare-response/", views.prepare_response, name="prepare-response"),
                # path("cover-letter/", views.edit_cover_letter, name="edit-cover-letter"),
                # path(
                #     "cover-letter/preview/",
                #     views.preview_cover_letter,
                #     name="preview-cover-letter",
                # ),
                # path("licence/", views.edit_licence, name="edit-licence"),
                # path("licence/preview/", views.preview_licence, name="preview-licence"),
                # path("authorisation/", views.authorisation, name="authorisation"),
                # path(
                #     "start-authorisation/", views.start_authorisation, name="start-authorisation"
                # ),
                # path(
                #     "cancel-authorisation/",
                #     views.cancel_authorisation,
                #     name="cancel-authorisation",
                # ),
                #
                # --- endorsements (TODO: ICMSLST-668)
                #
                # path("endorsements/add/", views.add_endorsement, name="add-endorsement"),
                # path(
                #     "endorsements/add-custom/",
                #     views.add_custom_endorsement,
                #     name="add-custom-endorsement",
                # ),
                # path(
                #     "endorsements/<int:endorsement_pk>/edit/",
                #     views.edit_endorsement,
                #     name="edit-endorsement",
                # ),
                # path(
                #     "endorsements/<int:endorsement_pk>/delete/",
                #     views.delete_endorsement,
                #     name="delete-endorsement",
                # ),
                #
                # --- Common to Importer/ILB Admin (TODO: probably part of ICMSLST-669?)
                #
                # path("view/", views.view_case, name="view-case"),
            ]
        ),
    ),
]
