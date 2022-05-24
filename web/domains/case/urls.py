from django.urls import include, path

from web.utils.pdf.types import DocumentTypes

from .views import (
    views_case_history,
    views_email,
    views_fir,
    views_misc,
    views_note,
    views_pdf,
    views_prepare_response,
    views_search,
    views_update_request,
    views_variation_request,
    views_view_case,
)

app_name = "case"

search_urls = [
    path("<str:mode>/", views_search.search_cases, name="search"),
    path(
        "<str:mode>/results/",
        views_search.search_cases,
        name="search-results",
        kwargs={"get_results": True},
    ),
    path(
        "search-download-spreadsheet",
        views_search.download_spreadsheet,
        name="search-download-spreadsheet",
    ),
    path(
        "search-reassign-case-owner",
        views_search.reassign_case_owner,
        name="search-reassign-case-owner",
    ),
    path(
        "search-actions/<int:application_pk>/",
        include(
            [
                path(
                    "reopen-case",
                    views_search.ReopenApplicationView.as_view(),
                    name="search-reopen-case",
                ),
                path(
                    "request-variation",
                    views_search.RequestVariationUpdateView.as_view(),
                    name="search-request-variation",
                ),
                path(
                    "open-variation",
                    views_search.RequestVariationOpenRequestView.as_view(),
                    name="search-open-variation",
                ),
            ]
        ),
    ),
]

note_urls = [
    path("list/", views_note.list_notes, name="list-notes"),
    path("add/", views_note.add_note, name="add-note"),
    path(
        "<int:note_pk>/",
        include(
            [
                path("edit/", views_note.edit_note, name="edit-note"),
                path("archive/", views_note.archive_note, name="archive-note"),
                path("unarchive/", views_note.unarchive_note, name="unarchive-note"),
                path(
                    "documents/",
                    include(
                        [
                            path("add/", views_note.add_note_document, name="add-note-document"),
                            path(
                                "<int:file_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views_note.view_note_document,
                                            name="view-note-document",
                                        ),
                                        path(
                                            "delete/",
                                            views_note.delete_note_document,
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
    path("manage/", views_misc.manage_case, name="manage"),
    path("take-ownership/", views_misc.take_ownership, name="take-ownership"),
    path("release-ownership/", views_misc.release_ownership, name="release-ownership"),
    path("manage-withdrawals/", views_misc.manage_withdrawals, name="manage-withdrawals"),
]

applicant_urls = [
    path("cancel/", views_misc.cancel_case, name="cancel"),
    path("withdraw/", views_misc.withdraw_case, name="withdraw-case"),
    path(
        "withdraw/<int:withdrawal_pk>/archive/",
        views_misc.archive_withdrawal,
        name="archive-withdrawal",
    ),
]

variation_request_urls = [
    path(
        "admin/",
        include(
            [
                path(
                    "manage/",
                    views_variation_request.VariationRequestManageView.as_view(),
                    name="variation-request-manage",
                ),
                path(
                    "<int:variation_request_pk>/",
                    include(
                        [
                            path(
                                "cancel/",
                                views_variation_request.VariationRequestCancelView.as_view(),
                                name="variation-request-cancel",
                            ),
                            path(
                                "request-update/",
                                views_variation_request.VariationRequestRequestUpdateView.as_view(),
                                name="variation-request-request-update",
                            ),
                            path(
                                "cancel-request-update/",
                                views_variation_request.VariationRequestCancelUpdateRequestView.as_view(),
                                name="variation-request-cancel-request-update",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "applicant/",
        include(
            [
                path(
                    "<int:variation_request_pk>/submit-update/",
                    views_variation_request.VariationRequestRespondToUpdateRequestView.as_view(),
                    name="variation-request-submit-update",
                )
            ]
        ),
    ),
]

further_information_requests_urls = [
    path("manage/", views_fir.manage_firs, name="manage-firs"),
    path("list/", views_fir.list_firs, name="list-firs"),
    path("add/", views_fir.add_fir, name="add-fir"),
    path(
        "<int:fir_pk>/",
        include(
            [
                path("edit/", views_fir.edit_fir, name="edit-fir"),
                path("respond/", views_fir.respond_fir, name="respond-fir"),
                path("delete/", views_fir.delete_fir, name="delete-fir"),
                path("withdraw/", views_fir.withdraw_fir, name="withdraw-fir"),
                path("close/", views_fir.close_fir, name="close-fir"),
                path(
                    "files/",
                    include(
                        [
                            path("add/", views_fir.add_fir_file, name="add-fir-file"),
                            path(
                                "response/add/",
                                views_fir.add_fir_response_file,
                                name="add-fir-response-file",
                            ),
                            path(
                                "<int:file_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views_fir.view_fir_file,
                                            name="view-fir-file",
                                        ),
                                        path(
                                            "delete/",
                                            views_fir.delete_fir_file,
                                            name="delete-fir-file",
                                        ),
                                        path(
                                            "response/delete/",
                                            views_fir.delete_fir_response_file,
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
    path("list/", views_update_request.list_update_requests, name="list-update-requests"),
    path("manage/", views_update_request.manage_update_requests, name="manage-update-requests"),
    path("respond/", views_update_request.respond_update_request, name="respond-update-request"),
    path(
        "<int:update_request_pk>/",
        include(
            [
                path(
                    "start/", views_update_request.start_update_request, name="start-update-request"
                ),
                path(
                    "close/", views_update_request.close_update_request, name="close-update-request"
                ),
            ]
        ),
    ),
]

authorisation_urls = [
    path("start/", views_misc.start_authorisation, name="start-authorisation"),
    path("cancel/", views_misc.cancel_authorisation, name="cancel-authorisation"),
    path("authorise-documents/", views_misc.authorise_documents, name="authorise-documents"),
    path("document-packs/", views_misc.view_document_packs, name="document-packs"),
]

case_progress_urls = [
    path(
        "check-document-generation/",
        views_misc.CheckCaseDocumentGenerationView.as_view(),
        name="check-document-generation",
    ),
    path(
        "recreate-case-documents/",
        views_misc.RecreateCaseDocumentsView.as_view(),
        name="recreate-case-documents",
    ),
]

ack_notification_urls = [
    path("", views_misc.ack_notification, name="ack-notification"),
]

email_urls = [
    path("manage/", views_email.manage_case_emails, name="manage-case-emails"),
    path("create/", views_email.create_case_email, name="create-case-email"),
    path(
        "<int:case_email_pk>/",
        include(
            [
                path("edit/", views_email.edit_case_email, name="edit-case-email"),
                path("archive/", views_email.archive_case_email, name="archive-case-email"),
                path(
                    "response/",
                    views_email.add_response_case_email,
                    name="add-response-case-email",
                ),
            ]
        ),
    ),
]

pdf_urls = [
    path(
        "licence/",
        include(
            [
                path(
                    "preview/",
                    views_pdf.PreviewLicenceView.as_view(),
                    name="licence-preview",
                    kwargs={"document_type": DocumentTypes.LICENCE_PREVIEW},
                ),
                path(
                    "pre-sign/",
                    views_pdf.PreviewLicenceView.as_view(),
                    name="licence-pre-sign",
                    kwargs={"document_type": DocumentTypes.LICENCE_PRE_SIGN},
                ),
            ]
        ),
    ),
    path(
        "cover-letter/",
        include(
            [
                path(
                    "preview/",
                    views_pdf.PreviewCoverLetterView.as_view(),
                    name="preview-cover-letter",
                ),
            ]
        ),
    ),
    path(
        "view-case-document/<int:object_pk>/<int:casedocumentreference_pk>",
        views_pdf.view_case_document,
        name="view-case-document",
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
                            path("view/", views_view_case.view_case, name="view"),
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
                                "prepare-response/",
                                views_prepare_response.prepare_response,
                                name="prepare-response",
                            ),
                            #
                            # Application Authorisation (import/export)
                            path("authorisation/", include(authorisation_urls)),
                            #
                            # Progress urls (import/export)
                            path("progress/", include(case_progress_urls)),
                            #
                            # Acknowledge Notification (import/export)
                            path("ack-notification/", include(ack_notification_urls)),
                            #
                            # Emails (import/export)
                            path("emails/", include(email_urls)),
                            #
                            # Variation request URLS:
                            path("variation-request/", include(variation_request_urls)),
                            #
                            # PDF generation URLs:
                            path("pdf/", include(pdf_urls)),
                            #
                            # Case history
                            path(
                                "case-history/",
                                views_case_history.CaseHistoryView.as_view(),
                                name="history",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
]
