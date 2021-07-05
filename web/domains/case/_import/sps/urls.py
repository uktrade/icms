from django.urls import include, path

from . import views

app_name = "sps"

contract_document = [
    path("add/", views.add_contract_document, name="add-contract-document"),
    path("view/", views.view_contract_document, name="view-contract-document"),
    path("edit/", views.edit_contract_document, name="edit-contract-document"),
    path("delete/", views.delete_contract_document, name="delete-contract-document"),
]

support_documents = [
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

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_sps, name="edit"),
                path("submit/", views.submit_sps, name="submit"),
                path("contract-document/", include(contract_document)),
                path("support-document/", include(support_documents)),
                # path("checklist/", views.manage_checklist, name="manage-checklist"),
            ],
        ),
    )
]
