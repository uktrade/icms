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
                path(
                    "edit-further-questions/<str:fq_type>/",
                    views.edit_further_questions_shared,
                    name="edit-further-questions-shared",
                ),
                path("submit/", views.submit_opt, name="submit"),
                path(
                    "document/",
                    include(
                        [
                            path("add/<str:file_type>", views.add_document, name="add-document"),
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
                path("checklist/", views.manage_checklist, name="manage-checklist"),
            ],
        ),
    )
]
