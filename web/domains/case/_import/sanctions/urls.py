from django.urls import include, path

from . import views

app_name = "sanctions"


goods_urls = [
    path("add/", views.add_goods, name="add-goods"),
    path("list/", views.SanctionsGoodsDetailView.as_view(), name="list-goods"),
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
                path(
                    "reset-goods-licence/",
                    views.reset_goods_licence,
                    name="reset-goods-licence",
                ),
            ]
        ),
    ),
]


supporting_document_urls = [
    path("add/", views.add_supporting_document, name="add-document"),
    path("list/", views.SanctionsSupportingDocumentsDetailView.as_view(), name="list-documents"),
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
            ]
        ),
    ),
]
