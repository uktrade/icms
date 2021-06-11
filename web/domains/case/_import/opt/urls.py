from django.urls import include, path

from . import views

app_name = "opt"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_opt, name="edit"),
                path(
                    "edit-compensating-products/",
                    views.edit_compensating_products,
                    name="edit-compensating-products",
                ),
                path(
                    "edit-temporary-exported-goods/",
                    views.edit_temporary_exported_goods,
                    name="edit-temporary-exported-goods",
                ),
                path(
                    "edit-further-questions/",
                    views.edit_further_questions,
                    name="edit-further-questions",
                ),
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
