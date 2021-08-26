from django.urls import include, path

from . import views, views_search

app_name = "case"

search_urls = [
    path("", views_search.search_cases, name="search"),
]

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
    path("manage/", views.manage_case, name="manage"),
    path("take-ownership/", views.take_ownership, name="take-ownership"),
    path("release-ownership/", views.release_ownership, name="release-ownership"),
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
                    "files/",
                    include(
                        [
                            path("add/", views.add_fir_file, name="add-fir-file"),
                            path(
                                "response/add/",
                                views.add_fir_response_file,
                                name="add-fir-response-file",
                            ),
                            path(
                                "<int:file_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views.view_fir_file,
                                            name="view-fir-file",
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_fir_file,
                                            name="delete-fir-file",
                                        ),
                                        path(
                                            "response/delete/",
                                            views.delete_fir_response_file,
                                            name="delete-fir-response-file",
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

update_requests_urls = [
    path("manage/", views.manage_update_requests, name="manage-update-requests"),
    path("respond/", views.respond_update_request, name="respond-update-request"),
    path(
        "<int:update_request_pk>/",
        include(
            [
                path("start/", views.start_update_request, name="start-update-request"),
                path("close/", views.close_update_request, name="close-update-request"),
            ]
        ),
    ),
]

authorisation_urls = [
    path("start/", views.start_authorisation, name="start-authorisation"),
    path("authorise-documents/", views.authorise_documents, name="authorise-documents"),
    path("cancel/", views.cancel_authorisation, name="cancel-authorisation"),
]

email_urls = [
    path("manage/", views.manage_case_emails, name="manage-case-emails"),
    path("create/", views.create_case_email, name="create-case-email"),
    path(
        "<int:case_email_pk>/",
        include(
            [
                path("edit/", views.edit_case_email, name="edit-case-email"),
                path("archive/", views.archive_case_email, name="archive-case-email"),
                path(
                    "response/",
                    views.add_response_case_email,
                    name="add-response-case-email",
                ),
            ]
        ),
    ),
]

urlpatterns = [
    path(
        "<casetype:case_type>/",
        include(
            [
                # search (import/export)
                path("search/", include(search_urls)),
                #
                path(
                    "<int:application_pk>/",
                    include(
                        [
                            # Common to applicant/ILB Admin (import/export/accessrequest)
                            path("view/", views.view_case, name="view"),
                            #
                            # further information requests ((import/export/accessrequest))
                            path("firs/", include(further_information_requests_urls)),
                            #
                            # applicant case management
                            path("applicant/", include(applicant_urls)),
                            #
                            # ILB Admin Case management (import/export)
                            path("admin/", include(admin_urls)),
                            #
                            # update requests
                            path("update-requests/", include(update_requests_urls)),
                            #
                            # notes (import/export)
                            path("notes/", include(note_urls)),
                            #
                            # misc stuff (import/export)
                            path(
                                "prepare-response/", views.prepare_response, name="prepare-response"
                            ),
                            #
                            # Application Authorisation (import/export)
                            path("authorisation/", include(authorisation_urls)),
                            #
                            # Emails (import/export)
                            path("emails/", include(email_urls)),
                        ]
                    ),
                ),
            ]
        ),
    )
]
