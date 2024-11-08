from django.conf import settings
from django.urls import include, path

from . import views

public_urls = [
    path("received/", views.ReceivedMailshotsView.as_view(), name="mailshot-received"),
    path(
        "<int:mailshot_pk>/",
        include(
            [
                path(
                    "received/",
                    views.MailshotReceivedDetailView.as_view(),
                    name="mailshot-detail-received",
                ),
                path(
                    "clear/", views.ClearMailshotFromWorkbasketView.as_view(), name="mailshot-clear"
                ),
                path(
                    "document/<int:document_pk>/view/",
                    views.view_document,
                    name="mailshot-view-document",
                ),
            ]
        ),
    ),
]

private_urls = [
    path("", views.MailshotListView.as_view(), name="mailshot-list"),
    path("new/", views.MailshotCreateView.as_view(), name="mailshot-new"),
    path(
        "<int:mailshot_pk>/",
        include(
            [
                path("", views.MailshotDetailView.as_view(), name="mailshot-detail"),
                path("edit/", views.MailshotEditView.as_view(), name="mailshot-edit"),
                path("cancel-draft/", views.cancel_mailshot, name="mailshot-cancel-draft"),
                path("publish-draft/", views.publish_mailshot, name="mailshot-publish-draft"),
                path("retract/", views.MailshotRetractView.as_view(), name="mailshot-retract"),
                path("republish/", views.republish, name="mailshot-republish"),
                path("document/add/", views.add_document, name="mailshot-add-document"),
                path(
                    "document/<int:document_pk>/delete/",
                    views.delete_document,
                    name="mailshot-delete-document",
                ),
            ]
        ),
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
