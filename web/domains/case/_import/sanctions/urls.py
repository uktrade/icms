from django.urls import path

from . import views

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
        "validation-summary/<int:pk>/",
        views.sanctions_validation_summary,
        name="sanctions-validation-summary",
    ),
    path(
        "application-submit/<int:pk>/",
        views.sanctions_application_submit,
        name="sanctions-submit",
    ),
]
