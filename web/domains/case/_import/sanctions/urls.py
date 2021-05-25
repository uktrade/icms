from django.urls import path

from . import views

app_name = "sanctions"

urlpatterns = [
    path("<int:application_pk>/edit/", views.edit_application, name="edit"),
    path("<int:pk>/add-goods/", views.add_goods, name="add-goods"),
    path("<int:application_pk>/goods/<int:goods_pk>/edit/", views.edit_goods, name="edit-goods"),
    path(
        "<int:application_pk>/goods/<int:goods_pk>/delete/", views.delete_goods, name="delete-goods"
    ),
    path("<int:pk>/add-document/", views.add_supporting_document, name="add-document"),
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
    path("application-submit/<int:pk>/", views.submit_sanctions, name="submit-sanctions"),
    # Management by ILB Admin
    path(
        "case/<int:pk>/sanction-emails/",
        views.manage_sanction_emails,
        name="manage-sanction-emails",
    ),
    path(
        "case/<int:pk>/sanction-emails/create/",
        views.create_sanction_email,
        name="create-sanction-email",
    ),
    path(
        "case/<int:application_pk>/sanction-emails/edit/<int:sanction_email_pk>/",
        views.edit_sanction_email,
        name="edit-sanction-email",
    ),
    path(
        "case/<int:application_pk>/sanction-emails/delete/<int:sanction_email_pk>/",
        views.delete_sanction_email,
        name="delete-sanction-email",
    ),
    path(
        "case/<int:application_pk>/sanction-emails/edit/<int:sanction_email_pk>/response/",
        views.add_response_sanction_email,
        name="add-response-sanction-email",
    ),
    path(
        "case/<int:application_pk>/goods/<int:goods_pk>/edit/",
        views.edit_goods_licence,
        name="edit-goods-licence",
    ),
]
