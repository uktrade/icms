from django.urls import path, re_path

from web.domains.firearms import views as firearms_views
from web.domains.importer import views

urlpatterns = [
    path("", views.ImporterListView.as_view(), name="importer-list"),
    path("<int:pk>/edit/", views.edit_importer, name="importer-edit"),
    re_path(
        "^(?P<entity>individual|organisation)/create/$",
        views.create_importer,
        name="importer-create",
    ),
    path("<int:pk>/", views.importer_detail_view, name="importer-view"),
    # contacts
    path("<int:pk>/contacts/add/", views.add_contact, name="importer-contact-add"),
    path(
        "<int:importer_pk>/contacts/<int:contact_pk>/delete/",
        views.delete_contact,
        name="importer-contact-delete",
    ),
    # firearms authorities
    path(
        "<int:pk>/firearms-authorities/create/",
        firearms_views.create_firearms_authorities,
        name="importer-firearms-authorities-create",
    ),
    path(
        "<int:importer_pk>/firearms-authorities/<int:firearms_authority_pk>/edit/",
        firearms_views.edit_firearms_authorities,
        name="importer-firearms-authorities-edit",
    ),
    path(
        "<int:importer_pk>/firearms-authorities/<int:firearms_authority_pk>/",
        firearms_views.detail_firearms_authorities,
        name="importer-firearms-authorities-detail",
    ),
    path(
        "<int:importer_pk>/firearms-authorities/<int:firearms_authority_pk>/archive/",
        firearms_views.archive_firearms_authorities,
        name="importer-firearms-authorities-archive",
    ),
    path(
        "<int:importer_pk>/firearms-authorities/<int:firearms_authority_pk>/unarchive/",
        firearms_views.unarchive_firearms_authorities,
        name="importer-firearms-authorities-unarchive",
    ),
    path(
        "<int:importer_pk>/firearms-authorities/<int:firearms_authority_pk>/files/<int:file_pk>/",
        firearms_views.archive_file_firearms_authorities,
        name="importer-firearms-authorities-file-archive",
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
    path("agent/<int:pk>/archive/", views.archive_agent, name="importer-agent-archive"),
    path("agent/<int:pk>/unarchive/", views.unarchive_agent, name="importer-agent-unarchive"),
    re_path(
        "^(?P<importer_pk>[0-9]+)/agent/(?P<entity>individual|organisation)/create/$",
        views.create_agent,
        name="importer-agent-create",
    ),
    path("lookup/postcode", views.list_postcode_addresses, name="importer-postcode-lookup"),
    path("lookup/company", views.list_companies, name="importer-company-lookup"),
]
