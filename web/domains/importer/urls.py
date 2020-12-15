from django.urls import path, re_path

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
    # section 5 authorities
    path(
        "<int:pk>/section5-authorities/create/",
        views.create_section5_authorities,
        name="importer-section5-authorities-create",
    ),
    path(
        "<int:importer_pk>/section5-authorities/<int:section5_authority_pk>/edit/",
        views.edit_section5_authorities,
        name="importer-section5-authorities-edit",
    ),
    path(
        "<int:importer_pk>/section5-authorities/<int:section5_authority_pk>/",
        views.detail_section5_authorities,
        name="importer-section5-authorities-detail",
    ),
    path(
        "<int:importer_pk>/section5-authorities/<int:section5_authority_pk>/archive/",
        views.archive_section5_authorities,
        name="importer-section5-authorities-archive",
    ),
    path(
        "<int:importer_pk>/section5-authorities/<int:section5_authority_pk>/unarchive/",
        views.unarchive_section5_authorities,
        name="importer-section5-authorities-unarchive",
    ),
    path(
        "<int:importer_pk>/section5-authorities/<int:section5_authority_pk>/files/<int:file_pk>/",
        views.archive_file_section5_authorities,
        name="importer-section5-authorities-file-archive",
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
    path("agent/<int:pk>/edit/", views.edit_agent, name="importer-agent-edit",),
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
