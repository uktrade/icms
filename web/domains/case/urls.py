from django.conf import settings
from django.urls import include, path

from web.types import DocumentTypes

from .views import (
    views_case_history,
    views_constabulary,
    views_documents,
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

public_search_urls = [
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
        "search-actions/<int:application_pk>/",
        include(
            [
                path(
                    "request-variation",
                    views_search.RequestVariationUpdateView.as_view(),
                    name="search-request-variation",
                ),
                path(
                    "copy-export-application",
                    views_search.CopyExportApplicationView.as_view(),
                    name="search-copy-export-application",
                ),
                path(
                    "copy-export-application-to-cat",
                    views_search.CreateCATemplateFromExportApplicationView.as_view(),
                    name="search-copy-export-app-to-cat",
                ),
            ]
        ),
    ),
]

private_search_urls = [
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
                    "open-variation",
                    views_search.RequestVariationOpenRequestView.as_view(),
                    name="search-open-variation",
                ),
                path(
                    "search-revoke-case",
                    views_search.RevokeCaseView.as_view(),
                    name="search-revoke-case",
                ),
            ]
        ),
    ),
]

# All notes urls are private
private_note_urls = [
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

# All admin urls are private
private_admin_urls = [
    path("take-ownership/", views_misc.take_ownership, name="take-ownership"),
    path("release-ownership/", views_misc.release_ownership, name="release-ownership"),
    path("reassign-ownership/", views_misc.reassign_ownership, name="reassign-ownership"),
    path("manage-withdrawals/", views_misc.manage_withdrawals, name="manage-withdrawals"),
]

# All applicant urls are public
public_applicant_urls = [
    path("cancel/", views_misc.cancel_case, name="cancel"),
    path("withdraw/", views_misc.withdraw_case, name="withdraw-case"),
    path(
        "withdraw/<int:withdrawal_pk>/archive/",
        views_misc.archive_withdrawal,
        name="archive-withdrawal",
    ),
    path("clear/", views_misc.ClearCaseFromWorkbasket.as_view(), name="clear"),
]

public_variation_request_urls = [
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

private_variation_request_urls = [
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
]

public_further_information_requests_urls = [
    path("list/", views_fir.list_firs, name="list-firs"),
    path(
        "<int:fir_pk>/",
        include(
            [
                path("respond/", views_fir.respond_fir, name="respond-fir"),
                path(
                    "files/",
                    include(
                        [
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
    # TODO: Revisit in ECIL-339
    #       Requires public endpoint as used in email link sent from public web.
    path("manage/", views_fir.manage_firs, name="manage-firs"),
]

private_further_information_requests_urls = [
    path("add/", views_fir.add_fir, name="add-fir"),
    path(
        "<int:fir_pk>/",
        include(
            [
                path("edit/", views_fir.edit_fir, name="edit-fir"),
                path("delete/", views_fir.delete_fir, name="delete-fir"),
                path("withdraw/", views_fir.withdraw_fir, name="withdraw-fir"),
                path("close/", views_fir.close_fir, name="close-fir"),
                path(
                    "files/",
                    include(
                        [
                            path("add/", views_fir.add_fir_file, name="add-fir-file"),
                            path(
                                "<int:file_pk>/",
                                include(
                                    [
                                        path(
                                            "delete/",
                                            views_fir.delete_fir_file,
                                            name="delete-fir-file",
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

public_update_requests_urls = [
    path(
        "<int:update_request_pk>/",
        include(
            [
                path(
                    "start/", views_update_request.start_update_request, name="start-update-request"
                ),
            ]
        ),
    ),
    path("respond/", views_update_request.respond_update_request, name="respond-update-request"),
]

private_update_requests_urls = [
    path("list/", views_update_request.list_update_requests, name="list-update-requests"),
    path("add/", views_update_request.add_update_request, name="add-update-request"),
    path(
        "<int:update_request_pk>/",
        include(
            [
                path("edit/", views_update_request.edit_update_request, name="edit-update-request"),
                path(
                    "delete/",
                    views_update_request.delete_update_request,
                    name="delete-update-request",
                ),
                path(
                    "close/", views_update_request.close_update_request, name="close-update-request"
                ),
            ]
        ),
    ),
]

# All authorisation urls are private
private_authorisation_urls = [
    path("start/", views_misc.start_authorisation, name="start-authorisation"),
    path("cancel/", views_misc.cancel_authorisation, name="cancel-authorisation"),
    path("authorise-documents/", views_misc.authorise_documents, name="authorise-documents"),
    path("document-packs/", views_misc.view_document_packs, name="document-packs"),
    path("quick-issue/", views_misc.QuickIssueApplicationView.as_view(), name="quick-issue"),
]

# All case_progress urls are private
private_case_progress_urls = [
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

# All email urls are private
private_email_urls = [
    path("manage/", views_email.manage_case_emails, name="manage-case-emails"),
    path("create/", views_email.create_draft_case_email, name="create-case-email"),
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

public_pdf_urls = [
    path(
        "view-case-document/<int:object_pk>/<int:casedocumentreference_pk>",
        views_pdf.view_case_document,
        name="view-case-document",
    ),
    path(
        "view-static-document/<int:file_pk>/",
        views_pdf.view_static_document,
        name="view-static-document",
    ),
]

private_pdf_urls = [
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
                    views_pdf.PresignLicenceView.as_view(),
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
                    name="cover-letter-preview",
                    kwargs={"document_type": DocumentTypes.COVER_LETTER_PREVIEW},
                ),
                path(
                    "pre-sign/",
                    views_pdf.PresignCoverLetterView.as_view(),
                    name="cover-letter-pre-sign",
                    kwargs={"document_type": DocumentTypes.COVER_LETTER_PRE_SIGN},
                ),
            ]
        ),
    ),
    path(
        "certificate/",
        include(
            [
                path(
                    "country/<int:country_pk>/preview/",
                    views_pdf.PreviewCertificateView.as_view(),
                    name="certificate-preview",
                    kwargs={"document_type": DocumentTypes.CERTIFICATE_PREVIEW},
                ),
                path(
                    "country/<int:country_pk>/pre-sign/",
                    views_pdf.PresignCertificateView.as_view(),
                    name="certificate-pre-sign",
                    kwargs={"document_type": DocumentTypes.CERTIFICATE_PRE_SIGN},
                ),
            ]
        ),
    ),
]

public_urls = [
    path(
        "<casetype:case_type>/",
        include(
            [
                # search (import/export)
                path("search/", include(public_search_urls)),
                #
                path(
                    "<int:application_pk>/",
                    include(
                        [
                            # TODO: Revisit in ECIL-339
                            #       Requires public endpoint as used in email link sent from public web.
                            path("admin/manage/", views_misc.manage_case, name="manage"),
                            # Common to applicant/ILB Admin (import/export/accessrequest)
                            path("view/", views_view_case.view_case, name="view"),
                            #
                            # further information requests ((import/export/accessrequest))
                            path("firs/", include(public_further_information_requests_urls)),
                            #
                            # applicant case management
                            path("applicant/", include(public_applicant_urls)),
                            #
                            # update requests
                            path("update-requests/", include(public_update_requests_urls)),
                            #
                            # View Issued Case Documents (import/export)
                            path(
                                "issued-case-documents/<int:issued_document_pk>/",
                                views_misc.ViewIssuedCaseDocumentsView.as_view(),
                                name="view-issued-case-documents",
                            ),
                            #
                            # Clear Issued Case Documents from workbasket (import/export)
                            path(
                                "issued-case-documents/<int:issued_document_pk>/clear/",
                                views_misc.ClearIssuedCaseDocumentsFromWorkbasket.as_view(),
                                name="clear-issued-case-documents",
                            ),
                            #
                            # Variation request URLS:
                            path("variation-request/", include(public_variation_request_urls)),
                            #
                            # PDF generation URLs:
                            path("pdf/", include(public_pdf_urls)),
                            #
                            # Case history - two url confs to handle which base template to use.
                            path(
                                "case-history/",
                                views_case_history.CaseHistoryView.as_view(),
                                name="ilb-case-history",
                                kwargs={"mode": "ilb"},
                            ),
                            path(
                                "applicant-case-history/",
                                views_case_history.CaseHistoryView.as_view(),
                                name="applicant-case-history",
                                kwargs={"mode": "applicant"},
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # TODO: Revisit in ECIL-295
    path(
        "download-dfl-case-documents/<uuid:code>/",
        views_documents.DownloadDFLCaseDocumentsFormView.as_view(),
        name="download-dfl-case-documents",
    ),
    path(
        "download-dfl-case-documents/<uuid:code>/regnerate-link/",
        views_documents.RegenerateDFLCaseDocumentsDownloadLinkView.as_view(),
        name="regenerate-dfl-case-documents-link",
    ),
    path(
        "download-case-email-documents/<uuid:code>/",
        views_documents.DownloadCaseEmailDocumentsFormView.as_view(),
        name="download-case-email-documents",
    ),
    path(
        "download-case-email-documents/<uuid:code>/regnerate-link/",
        views_documents.RegenerateCaseEmailDocumentsDownloadLinkView.as_view(),
        name="regenerate-case-email-documents-link",
    ),
]

private_urls = [
    path(
        "<casetype:case_type>/",
        include(
            [
                # search (import/export)
                path("search/", include(private_search_urls)),
                #
                path(
                    "<int:application_pk>/",
                    include(
                        [
                            #
                            # further information requests ((import/export/accessrequest))
                            path("firs/", include(private_further_information_requests_urls)),
                            #
                            # ILB Admin Case management (import/export)
                            path("admin/", include(private_admin_urls)),
                            #
                            # update requests
                            path("update-requests/", include(private_update_requests_urls)),
                            #
                            # notes (import/export)
                            path("notes/", include(private_note_urls)),
                            #
                            # misc stuff (import/export)
                            path(
                                "prepare-response/",
                                views_prepare_response.prepare_response,
                                name="prepare-response",
                            ),
                            #
                            # Application Authorisation (import/export)
                            path("authorisation/", include(private_authorisation_urls)),
                            #
                            # Progress urls (import/export)
                            path("progress/", include(private_case_progress_urls)),
                            #
                            # Emails (import/export)
                            path("emails/", include(private_email_urls)),
                            #
                            # Variation request URLS:
                            path("variation-request/", include(private_variation_request_urls)),
                            #
                            # PDF generation URLs:
                            path("pdf/", include(private_pdf_urls)),
                            path(
                                "documents/<int:doc_pack_pk>/",
                                views_constabulary.ConstabularyDocumentView.as_view(),
                                name="constabulary-doc",
                            ),
                            path(
                                "documents/<int:doc_pack_pk>/download/<int:cdr_pk>/",
                                views_constabulary.ConstabularyDocumentDownloadView.as_view(),
                                name="constabulary-doc-download",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
