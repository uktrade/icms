from django.conf import settings
from django.urls import path

from . import views

public_urls = [
    path("list/user/", views.ExporterListUserView.as_view(), name="user-exporter-list"),
    path("<int:pk>/", views.detail_exporter, name="exporter-view"),
    path("<int:pk>/edit/", views.edit_exporter, name="exporter-edit"),
    path(
        "<int:org_pk>/user/<int:user_pk>/object_perms/",
        views.edit_user_exporter_permissions,
        name="edit-user-exporter-permissions",
    ),
    # offices
    path("<int:pk>/offices/create/", views.create_office, name="exporter-office-create"),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/edit/",
        views.edit_office,
        name="exporter-office-edit",
    ),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/archive/",
        views.archive_office,
        name="exporter-office-archive",
    ),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/unarchive/",
        views.unarchive_office,
        name="exporter-office-unarchive",
    ),
    # Exporter Agents
    path("agent/<int:pk>/edit/", views.edit_agent, name="exporter-agent-edit"),
]

private_urls = [
    path("", views.ExporterListAdminView.as_view(), name="exporter-list"),
    path("create/", views.create_exporter, name="exporter-create"),
    # Exporter Agents
    path("<int:exporter_pk>/agent/create/", views.create_agent, name="exporter-agent-create"),
    path("agent/<int:pk>/archive/", views.archive_agent, name="exporter-agent-archive"),
    path("agent/<int:pk>/unarchive/", views.unarchive_agent, name="exporter-agent-unarchive"),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
