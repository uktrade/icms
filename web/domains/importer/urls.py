from django.urls import path, re_path

from web.domains.importer import views
from web.domains.importer.forms import AgentIndividualForm, AgentOrganisationForm

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
    path("agent/<int:pk>/edit/", views.AgentEditView.as_view(), name="importer-agent-edit",),
    path(
        "agent/<int:pk>/archive/", views.AgentArchiveView.as_view(), name="importer-agent-archive",
    ),
    path(
        "agent/<int:pk>/unarchive/",
        views.AgentUnArchiveView.as_view(),
        name="importer-agent-unarchive",
    ),
    path(
        "<int:importer_id>/agent/individual/create/",
        views.AgentCreateView.as_view(),
        {"form_class": AgentIndividualForm},
        name="importer-agent-individual-create",
    ),
    path(
        "<int:importer_id>/agent/organisation/create/",
        views.AgentCreateView.as_view(),
        {"form_class": AgentOrganisationForm},
        name="importer-agent-organisation-create",
    ),
    path("lookup/postcode", views.list_postcode_addresses, name="importer-postcode-lookup"),
    path("lookup/company", views.list_companies, name="importer-company-lookup"),
]
