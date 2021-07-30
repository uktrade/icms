from django.urls import include, path

from . import views

app_name = "ironsteel"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_ironsteel, name="edit"),
                path("submit/", views.submit_ironsteel, name="submit"),
                path(
                    "document/",
                    include(
                        [
                            path("add/", views.add_document, name="add-document"),
                            path(
                                "<int:document_pk>/",
                                include(
                                    [
                                        path("view/", views.view_document, name="view-document"),
                                        path(
                                            "delete/", views.delete_document, name="delete-document"
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
