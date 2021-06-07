from django.urls import include, path

from . import views

app_name = "fa"

# Firearms and Ammunition - Common urls
urlpatterns = [
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
                                views.list_import_contacts,
                                name="list-import-contacts",
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
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "constabulary-emails/",
                    include(
                        [
                            path(
                                "manage/",
                                views.manage_constabulary_emails,
                                name="manage-constabulary-emails",
                            ),
                            path(
                                "create/",
                                views.create_constabulary_email,
                                name="create-constabulary-email",
                            ),
                            path(
                                "<int:constabulary_email_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/",
                                            views.edit_constabulary_email,
                                            name="edit-constabulary-email",
                                        ),
                                        path(
                                            "archive/",
                                            views.archive_constabulary_email,
                                            name="archive-constabulary-email",
                                        ),
                                        path(
                                            "response/",
                                            views.add_response_constabulary_email,
                                            name="add-response-constabulary-email",
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
                        ],
                    ),
                ),
            ]
        ),
    )
]
