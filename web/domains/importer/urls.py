#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from web.domains.importer import views
from web.domains.importer.forms import (
    AgentIndividualForm,
    AgentOrganisationForm,
    ImporterIndividualForm,
    ImporterOrganisationForm,
)

urlpatterns = [
    path("", views.ImporterListView.as_view(), name="importer-list"),
    path("<int:pk>/edit/", views.ImporterEditView.as_view(), name="importer-edit"),
    path(
        "individual/create/",
        views.ImporterCreateView.as_view(),
        {"form_class": ImporterIndividualForm},
        name="importer-individual-create",
    ),
    path(
        "organisation/create/",
        views.ImporterCreateView.as_view(),
        {"form_class": ImporterOrganisationForm},
        name="importer-organisation-create",
    ),
    path("<int:pk>/", views.importer_detail_view, name="importer-view"),
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
