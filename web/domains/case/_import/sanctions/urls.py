from django.urls import include, path

from . import views

app_name = "sanctions"


goods_urls = [
    path("add/", views.add_goods, name="add-goods"),
    path(
        "<int:goods_pk>/",
        include(
            [
                path("edit/", views.edit_goods, name="edit-goods"),
                path("delete/", views.delete_goods, name="delete-goods"),
                # Management url
                path(
                    "edit-goods-licence/",
                    views.edit_goods_licence,
                    name="edit-goods-licence",
                ),
            ]
        ),
    ),
]


supporting_document_urls = [
    path("add/", views.add_supporting_document, name="add-document"),
    path(
        "<int:document_pk>/",
        include(
            [
                path("view/", views.view_supporting_document, name="view-supporting-document"),
                path("delete/", views.delete_supporting_document, name="delete-document"),
            ]
        ),
    ),
]


sanction_urls = [
    path("manage/", views.manage_sanction_emails, name="manage-sanction-emails"),
    path(
        "create/",
        views.create_sanction_email,
        name="create-sanction-email",
    ),
    path(
        "<int:sanction_email_pk>/",
        include(
            [
                path(
                    "edit/",
                    views.edit_sanction_email,
                    name="edit-sanction-email",
                ),
                path(
                    "delete/",
                    views.delete_sanction_email,
                    name="delete-sanction-email",
                ),
                path(
                    "add-response/",
                    views.add_response_sanction_email,
                    name="add-response-sanction-email",
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
                # Applicant urls
                path("edit/", views.edit_application, name="edit"),
                path("submit/", views.submit_sanctions, name="submit-sanctions"),
                path("goods/", include(goods_urls)),
                path("support-document/", include(supporting_document_urls)),
                # Management urls
                path("sanction-email/", include(sanction_urls)),
            ]
        ),
    ),
]
