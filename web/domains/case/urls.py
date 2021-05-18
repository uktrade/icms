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

applicant_urls = [
    path("withdraw/", views.withdraw_case, name="withdraw-case"),
    path(
        "withdraw/<int:withdrawal_pk>/archive/", views.archive_withdrawal, name="archive-withdrawal"
    ),
]

further_information_requests_urls = [
    path("manage/", views.manage_firs, name="manage-firs"),
    path("list/", views.list_firs, name="list-firs"),
    path("add/", views.add_fir, name="add-fir"),
    path(
        "<int:fir_pk>/",
        include(
            [
                path("edit/", views.edit_fir, name="edit-fir"),
                path("respond/", views.respond_fir, name="respond-fir"),
                path("delete/", views.delete_fir, name="delete-fir"),
                path("withdraw/", views.withdraw_fir, name="withdraw-fir"),
                path("close/", views.close_fir, name="close-fir"),
                path(
                    "files/<int:file_pk>/delete/",
                    views.delete_fir_file,
                    name="delete-fir-file",
                ),
            ]
        ),
    ),
]

urlpatterns = [
    path(
        "<casetype:case_type>/<int:application_pk>/",
        include(
            [
                # --- Common to applicant/ILB Admin (import/export/accessrequest)
                #
                path("view/", views.view_case, name="view"),
                #
                # --- further information requests ((import/export/accessrequest))
                #
                path("firs/", include(further_information_requests_urls)),
                #
                # --- applicant case management
                #
                path("applicant/", include(applicant_urls)),
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
            ]
        ),
    ),
]
