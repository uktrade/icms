from django.urls import include, path

from . import views

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
            ]
        ),
    ),
]
