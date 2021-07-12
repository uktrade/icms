from django.urls import include, path

from . import views

app_name = "wood"

supporting_document_urls = [
    path("add/", views.add_supporting_document, name="add-supporting-document"),
    path(
        "<int:document_pk>/",
        include(
            [
                path("view/", views.view_supporting_document, name="view-supporting-document"),
                path(
                    "delete/", views.delete_supporting_document, name="delete-supporting-document"
                ),
            ]
        ),
    ),
]


contract_document_urls = [
    path("add/", views.add_contract_document, name="add-contract-document"),
    path(
        "<int:document_pk>/",
        include(
            [
                path("view/", views.view_contract_document, name="view-contract-document"),
                path("delete/", views.delete_contract_document, name="delete-contract-document"),
                path("edit/", views.edit_contract_document, name="edit-contract-document"),
            ]
        ),
    ),
]

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                # Applicant urls
                path("edit/", views.edit_wood_quota, name="edit"),
                path("submit/", views.submit_wood_quota, name="submit-quota"),
                path("contract-document/", include(contract_document_urls)),
                path("support-document/", include(supporting_document_urls)),
                # Management urls
                path("checklist/", views.manage_checklist, name="manage-checklist"),
                path("edit-goods-licence/", views.edit_goods, name="edit-goods-licence"),
            ],
        ),
    ),
]
