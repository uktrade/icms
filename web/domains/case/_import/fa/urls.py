from django.urls import include, path

from . import views

app_name = "fa"

# Firearms and Ammunition - Common urls
urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                # TODO: Add import contacts
                # path("import-contacts/", include([])),
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
                                            "delete/",
                                            views.delete_constabulary_email,
                                            name="delete-constabulary-email",
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
            ]
        ),
    )
]
