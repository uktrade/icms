from django.urls import include, path

from . import views

app_name = "textiles"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_textiles, name="edit"),
                path("submit/", views.submit_textiles, name="submit"),
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
                path("checklist/", views.manage_checklist, name="manage-checklist"),
                path("edit-goods-licence/", views.edit_goods_licence, name="edit-goods-licence"),
            ],
        ),
    )
]
