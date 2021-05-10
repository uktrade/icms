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

urlpatterns = [
    path(
        "<casetype:case_type>/<int:application_pk>/",
        include(
            [
                # --- further information requests (TODO: ICMSLST-665)
                #     NOTE: these are the only ones that take AcceptRequest
                #
                # path("case/<int:application_pk>/firs/list/", views.list_firs, name="list-firs"),
                # path("case/<int:application_pk>/firs/", views.manage_firs, name="manage-firs"),
                # path("case/<int:application_pk>/firs/add/", views.add_fir, name="add-fir"),
                # path("case/<int:application_pk>/firs/<int:fir_pk>/edit/", views.edit_fir, name="edit-fir"),
                # path(
                #     "case/<int:application_pk>/firs/<int:fir_pk>/respond/",
                #     views.respond_fir,
                #     name="respond-fir",
                # ),
                # path(
                #     "case/<int:application_pk>/firs/<int:fir_pk>/archive/",
                #     views.archive_fir,
                #     name="archive-fir",
                # ),
                # path(
                #     "case/<int:application_pk>/firs/<int:fir_pk>/withdraw/",
                #     views.withdraw_fir,
                #     name="withdraw-fir",
                # ),
                # path("case/<int:application_pk>/firs/<int:fir_pk>/close/", views.close_fir, name="close-fir"),
                # path(
                #     "case/<int:application_pk>/firs/<int:fir_pk/files/<int:file_pk/archive/",
                #     views.archive_fir_file,
                #     name="archive-fir-file",
                # ),
                #
                # --- applicant case management (TODO: ICMSLST-666)
                # path("case/<int:pk>/withdraw/", views.withdraw_case, name="withdraw-case"),
                # path(
                #     "case/<int:application_pk>/withdraw/<int:withdrawal_pk>/archive/",
                #     views.archive_withdrawal,
                #     name="archive-withdrawal",
                # ),
                #
                # -- ILB Admin Case management (TODO: ICMSLST-667)
                #
                # path("case/<int:pk>/take_ownership/", views.take_ownership, name="take-ownership"),
                # path("case/<int:pk>/release_ownership/", views.release_ownership, name="release-ownership"),
                # path("case/<int:pk>/management/", views.manage_case, name="case-management"),
                # path("case/<int:pk>/withdrawals/", views.manage_withdrawals, name="manage-withdrawals"),
                # path(
                #     "case/<int:pk>/update-requests/",
                #     views.manage_update_requests,
                #     name="manage-update-requests",
                # ),
                # path(
                #     "case/<int:application_pk>/update-requests/<int:update_request_pk>/close/",
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
                # path("case/<int:pk>/prepare-response/", views.prepare_response, name="prepare-response"),
                # path("case/<int:pk>/cover-letter/", views.edit_cover_letter, name="edit-cover-letter"),
                # path(
                #     "case/<int:pk>/cover-letter/preview/",
                #     views.preview_cover_letter,
                #     name="preview-cover-letter",
                # ),
                # path("case/<int:pk>/licence/", views.edit_licence, name="edit-licence"),
                # path("case/<int:pk>/licence/preview/", views.preview_licence, name="preview-licence"),
                # path("case/<int:pk>/authorisation/", views.authorisation, name="authorisation"),
                # path(
                #     "case/<int:pk>/start-authorisation/", views.start_authorisation, name="start-authorisation"
                # ),
                # path(
                #     "case/<int:pk>/cancel-authorisation/",
                #     views.cancel_authorisation,
                #     name="cancel-authorisation",
                # ),
                #
                # --- endorsements (TODO: ICMSLST-668)
                #
                # path(
                #     "case/<int:pk>/endorsements/add/",
                #     views.add_endorsement,
                #     name="add-endorsement",
                # ),
                # path(
                #     "case/<int:pk>/endorsements/add-custom/",
                #     views.add_custom_endorsement,
                #     name="add-custom-endorsement",
                # ),
                # path(
                #     "case/<int:application_pk>/endorsements/<int:endorsement_pk>/edit/",
                #     views.edit_endorsement,
                #     name="edit-endorsement",
                # ),
                # path(
                #     "case/<int:application_pk>/endorsements/<int:endorsement_pk>/delete/",
                #     views.delete_endorsement,
                #     name="delete-endorsement",
                # ),
                #
                # --- Common to Importer/ILB Admin (TODO: probably part of ICMSLST-669?)
                #
                # path("case/<int:pk>/view/", views.view_case, name="view-case"),
            ]
        ),
    ),
]
