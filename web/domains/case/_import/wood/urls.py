from django.urls import path

from . import views

app_name = "wood"

urlpatterns = [
    path("quota/<int:application_pk>/edit/", views.edit_wood_quota, name="edit"),
    path("quota/<int:pk>/submit/", views.submit_wood_quota, name="submit-quota"),
    path("<int:application_pk>/checklist/", views.manage_checklist, name="manage-checklist"),
    # supporting documents
    path(
        "quota/<int:pk>/add-supporting-document/",
        views.add_supporting_document,
        name="add-supporting-document",
    ),
    path(
        "quota/<int:application_pk>/view-supporting-document/<int:document_pk>/",
        views.view_supporting_document,
        name="view-supporting-document",
    ),
    path(
        "quota/<int:application_pk>/delete-supporting-document/<int:document_pk>/",
        views.delete_supporting_document,
        name="delete-supporting-document",
    ),
    # contract documents
    path(
        "quota/<int:pk>/add-contract-document/",
        views.add_contract_document,
        name="add-contract-document",
    ),
    path(
        "quota/<int:application_pk>/view-contract-document/<int:document_pk>/",
        views.view_contract_document,
        name="view-contract-document",
    ),
    path(
        "quota/<int:application_pk>/delete-contract-document/<int:document_pk>/",
        views.delete_contract_document,
        name="delete-contract-document",
    ),
    path(
        "quota/<int:application_pk>/edit-contract-document/<int:document_pk>/",
        views.edit_contract_document,
        name="edit-contract-document",
    ),
    path("quota/<int:pk>/edit-goods-licence/", views.edit_goods, name="edit-goods-licence"),
]
