from django.urls import path

from . import views

app_name = "sanctions"

urlpatterns = [
    path(
        "<int:pk>/edit/",
        views.edit_sanctions_and_adhoc_licence_application,
        name="edit-sanctions-and-adhoc-licence-application",
    ),
    path(
        "<int:pk>/add-goods/",
        views.add_goods,
        name="add-goods",
    ),
    path(
        "<int:application_pk>/goods/<int:goods_pk>/edit/",
        views.edit_goods,
        name="edit-goods",
    ),
    path(
        "<int:application_pk>/goods/<int:goods_pk>/delete/",
        views.delete_goods,
        name="delete-goods",
    ),
    path(
        "<int:pk>/add-document/",
        views.add_supporting_document,
        name="add-document",
    ),
    path(
        "<int:application_pk>/view-supporting-document/<int:document_pk>/",
        views.view_supporting_document,
        name="view-supporting-document",
    ),
    path(
        "<int:application_pk>/documents/<int:document_pk>/delete/",
        views.delete_supporting_document,
        name="delete-document",
    ),
    path(
        "validation-summary/<int:pk>/",
        views.sanctions_validation_summary,
        name="sanctions-validation-summary",
    ),
    path(
        "application-submit/<int:pk>/",
        views.submit_sanctions,
        name="submit-sanctions",
    ),
]
