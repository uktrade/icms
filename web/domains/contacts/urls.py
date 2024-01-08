from django.urls import include, path

from . import views

app_name = "contacts"

urlpatterns = [
    path(
        "<orgtype:org_type>/<int:org_pk>/",
        include(
            [
                path("add/", views.add, name="add"),
                path("<int:contact_pk>/delete/", views.delete, name="delete"),
                path(
                    "invite-contact/",
                    views.InviteOrgContactView.as_view(),
                    name="invite-org-contact",
                ),
            ]
        ),
    ),
    path(
        "accept-org-invite/<uuid:code>/",
        views.AcceptOrgContactInviteView.as_view(),
        name="accept-org-invite",
    ),
]
