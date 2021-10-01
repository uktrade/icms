from django.urls import include, path

from . import views

document_urls = [
    path(
        "document/",
        include(
            [
                path("add/", views.add_document, name="mailshot-add-document"),
                path(
                    "<int:document_pk>/",
                    include(
                        [
                            path("view/", views.view_document, name="mailshot-view-document"),
                            path("delete/", views.delete_document, name="mailshot-delete-document"),
                        ]
                    ),
                ),
            ]
        ),
    ),
]


urlpatterns = [
    path("", views.MailshotListView.as_view(), name="mailshot-list"),
    path("new/", views.MailshotCreateView.as_view(), name="mailshot-new"),
    path("received/", views.ReceivedMailshotsView.as_view(), name="mailshot-received"),
    path(
        "<int:mailshot_pk>/",
        include(
            [
                path("", views.MailshotDetailView.as_view(), name="mailshot-detail"),
                path("edit/", views.MailshotEditView.as_view(), name="mailshot-edit"),
                path("retract/", views.MailshotRetractView.as_view(), name="mailshot-retract"),
                path(
                    "received/",
                    views.MailshotReceivedDetailView.as_view(),
                    name="mailshot-detail-received",
                ),
                path("document/", include(document_urls)),
            ]
        ),
    ),
]
