from django.conf import settings
from django.urls import path

from web.domains.firearms import views as firearms_views
from web.domains.importer import views

public_urls = [
    path("list/user/", views.ImporterListUserView.as_view(), name="user-importer-list"),
    path("<int:pk>/edit/", views.edit_importer, name="importer-edit"),
    path("<int:pk>/", views.importer_detail_view, name="importer-view"),
    path(
        "<int:org_pk>/user/<int:user_pk>/object_perms/",
        views.edit_user_importer_permissions,
        name="edit-user-importer-permissions",
    ),
    # offices
    path("<int:pk>/offices/create/", views.create_office, name="importer-office-create"),
    path(
        "<int:importer_pk>/offices/<int:office_pk>/edit/",
        views.edit_office,
        name="importer-office-edit",
    ),
    path(
        "<int:importer_pk>/offices/<int:office_pk>/archive/",
        views.archive_office,
        name="importer-office-archive",
    ),
    path(
        "<int:importer_pk>/offices/<int:office_pk>/unarchive/",
        views.unarchive_office,
        name="importer-office-unarchive",
    ),
    # Importer Agents
    path("agent/<int:pk>/edit/", views.edit_agent, name="importer-agent-edit"),
]

private_urls = [
    path("", views.ImporterListAdminView.as_view(), name="importer-list"),
    path("list/reg/", views.ImporterListRegulatorView.as_view(), name="regulator-importer-list"),
    path(
        "list/reg/<int:importer_pk>/",
        views.ImporterDetailRegulatorView.as_view(),
        name="regulator-importer-detail",
    ),
    path("<entitytype:entity_type>/create/", views.create_importer, name="importer-create"),
    # firearms authority
    path(
        "<int:pk>/firearms/create/", firearms_views.create_firearms, name="importer-firearms-create"
    ),
    path("firearms/<int:pk>/edit/", firearms_views.edit_firearms, name="importer-firearms-edit"),
    path("firearms/<int:pk>/view/", firearms_views.view_firearms, name="importer-firearms-view"),
    path(
        "firearms/<int:pk>/archive/",
        firearms_views.archive_firearms,
        name="importer-firearms-archive",
    ),
    path(
        "firearms/<int:pk>/unarchive/",
        firearms_views.unarchive_firearms,
        name="importer-firearms-unarchive",
    ),
    # firearms authority - documents
    path(
        "firearms/<int:pk>/add-document/",
        firearms_views.add_document_firearms,
        name="importer-firearms-add-document",
    ),
    path(
        "firearms/<int:firearms_pk>/view-document/<int:document_pk>/",
        firearms_views.view_document_firearms,
        name="importer-firearms-view-document",
    ),
    path(
        "firearms/<int:firearms_pk>/delete-document/<int:document_pk>/",
        firearms_views.delete_document_firearms,
        name="importer-firearms-delete-document",
    ),
    # section 5 authority
    path("<int:pk>/section5/create/", views.create_section5, name="importer-section5-create"),
    path("section5/<int:pk>/edit/", views.edit_section5, name="importer-section5-edit"),
    path("section5/<int:pk>/view/", views.view_section5, name="importer-section5-view"),
    path("section5/<int:pk>/archive/", views.archive_section5, name="importer-section5-archive"),
    path(
        "section5/<int:pk>/unarchive/", views.unarchive_section5, name="importer-section5-unarchive"
    ),
    # section 5 authority - documents
    path(
        "section5/<int:pk>/add-document/",
        views.add_document_section5,
        name="importer-section5-add-document",
    ),
    path(
        "section5/<int:section5_pk>/view-document/<int:document_pk>/",
        views.view_document_section5,
        name="importer-section5-view-document",
    ),
    path(
        "section5/<int:section5_pk>/delete-document/<int:document_pk>/",
        views.delete_document_section5,
        name="importer-section5-delete-document",
    ),
    # Importer Agents
    path("agent/<int:pk>/archive/", views.archive_agent, name="importer-agent-archive"),
    path("agent/<int:pk>/unarchive/", views.unarchive_agent, name="importer-agent-unarchive"),
    path(
        "<int:importer_pk>/agent/<entitytype:entity_type>/create/",
        views.create_agent,
        name="importer-agent-create",
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
