from django.urls import path

from . import views

urlpatterns = [
    # obsolete calibre group
    path("", views.ObsoleteCalibreListView.as_view(), name="obsolete-calibre-group-list"),
    path("create/", views.create_obsolete_calibre_group, name="obsolete-calibre-group-create"),
    path("<int:pk>/edit/", views.edit_obsolete_calibre_group, name="obsolete-calibre-group-edit"),
    path("<int:pk>/", views.view_obsolete_calibre_group, name="obsolete-calibre-group-view"),
    path(
        "archive/<int:pk>/",
        views.archive_obsolete_calibre_group,
        name="obsolete-calibre-group-archive",
    ),
    path(
        "unarchive/<int:pk>/",
        views.unarchive_obsolete_calibre_group,
        name="obsolete-calibre-group-unarchive",
    ),
    path("order/", views.order_obsolete_calibre_group, name="obsolete-calibre-group-order"),
    # obsolete calibre
    path(
        "<int:calibre_group_pk>/create/",
        views.create_obsolete_calibre,
        name="obsolete-calibre-create",
    ),
    path(
        "<int:calibre_group_pk>/edit/<int:calibre_pk>/",
        views.edit_obsolete_calibre,
        name="obsolete-calibre-edit",
    ),
    path(
        "<int:calibre_group_pk>/archive/<int:calibre_pk>/",
        views.archive_obsolete_calibre,
        name="obsolete-calibre-archive",
    ),
    path(
        "<int:calibre_group_pk>/unarchive/<int:calibre_pk>/",
        views.unarchive_obsolete_calibre,
        name="obsolete-calibre-unarchive",
    ),
    path(
        "<int:calibre_group_pk>/order/",
        views.order_obsolete_calibre,
        name="obsolete-calibre-order",
    ),
]
