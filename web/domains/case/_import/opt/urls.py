from django.urls import include, path

from . import views

app_name = "opt"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_opt, name="edit"),
                path("submit/", views.submit_opt, name="submit"),
                path(
                    "supporting-document/",
                    include(
                        [
                            path(
                                "add/",
                                views.add_supporting_document,
                                name="add-supporting-document",
                            ),
                            path(
                                "<int:document_pk>/",
                                include(
                                    [
                                        path(
                                            "view/",
                                            views.view_supporting_document,
                                            name="view-supporting-document",
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_supporting_document,
                                            name="delete-supporting-document",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ],
        ),
    )
]
