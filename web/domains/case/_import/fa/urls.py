from django.conf import settings
from django.urls import include, path

from . import views

app_name = "fa"

# Firearms and Ammunition - Common urls
public_urls = [
    path(
        "<int:application_pk>/",
        include(
            [
                path(
                    "import-contacts/",
                    include(
                        [
                            path(
                                "manage/",
                                views.manage_import_contacts,
                                name="manage-import-contacts",
                            ),
                            path(
                                "<entity>/",
                                include(
                                    [
                                        path(
                                            "create/",
                                            views.create_import_contact,
                                            name="create-import-contact",
                                        ),
                                        path(
                                            "<int:contact_pk>/edit/",
                                            views.edit_import_contact,
                                            name="edit-import-contact",
                                        ),
                                        path(
                                            "<int:contact_pk>/delete/",
                                            views.delete_import_contact,
                                            name="delete-import-contact",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "certificates/",
                    include(
                        [
                            path("manage/", views.manage_certificates, name="manage-certificates"),
                            path("create/", views.create_certificate, name="create-certificate"),
                            path(
                                "<int:certificate_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/", views.edit_certificate, name="edit-certificate"
                                        ),
                                        path(
                                            "view/",
                                            views.view_certificate_document,
                                            name="view-certificate-document",
                                        ),
                                        path(
                                            "archive/",
                                            views.archive_certificate,
                                            name="archive-certificate",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "verified-certificates/<int:authority_pk>/",
                    include(
                        [
                            path(
                                "add/",
                                views.add_authority,
                                name="add-authority",
                            ),
                            path(
                                "delete/",
                                views.delete_authority,
                                name="delete-authority",
                            ),
                            path(
                                "view/",
                                views.view_authority,
                                name="view-authority",
                            ),
                            path(
                                "document/<int:document_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views.view_authority_document,
                                            name="view-authority-document",
                                        )
                                    ]
                                ),
                            ),
                        ],
                    ),
                ),
                # Firearm workbasket links
                path(
                    "provide-report/",
                    include(
                        [
                            path("", views.provide_report, name="provide-report"),
                            path("repoen/", views.reopen_report, name="reopen-report"),
                            path(
                                "create/",
                                views.create_report,
                                name="create-report",
                            ),
                            path(
                                "<int:report_pk>/edit/",
                                views.edit_report,
                                name="edit-report",
                            ),
                            path(
                                "<int:report_pk>/delete/",
                                views.delete_report,
                                name="delete-report",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
]

private_urls = [
    path(
        "<int:application_pk>/",
        include(
            [
                # Firearm workbasket links
                path(
                    "provide-report/",
                    include(
                        [
                            # private
                            path(
                                "view/",
                                views.ViewFirearmsReportDetailView.as_view(),
                                name="view-report",
                            )
                        ]
                    ),
                ),
            ]
        ),
    )
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
