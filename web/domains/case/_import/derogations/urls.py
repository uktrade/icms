from django.urls import include, path

from . import views

app_name = "derogations"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_derogations, name="edit"),
                path(
                    "add-supporting-document/",
                    views.add_supporting_document,
                    name="add-supporting-document",
                ),
                path(
                    "view-supporting-document/<int:document_pk>/",
                    views.view_supporting_document,
                    name="view-supporting-document",
                ),
                path(
                    "delete-supporting-document/<int:document_pk>/",
                    views.delete_supporting_document,
                    name="delete-supporting-document",
                ),
                path("submit/", views.submit_derogations, name="submit-derogations"),
                # ILB Admin Case management
                path("checklist/", views.manage_checklist, name="manage-checklist"),
                path("edit-goods-licence/", views.edit_goods_licence, name="edit-goods-licence"),
            ]
        ),
    ),
]
