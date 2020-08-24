#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from web.domains.importer import views
from web.domains.importer.forms import ImporterIndividualForm, ImporterOrganisationForm

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
    path(
        "<int:importer_id>/agent/<int:pk>/edit",
        views.ImporterEditView.as_view(),
        name="importer-agent-edit",
    ),
    path(
        "<int:importer_id>/agent/new/",
        views.ImporterCreateView.as_view(),
        name="importer-agent-new",
    ),
    path("lookup/postcode", views.list_postcode_addresses, name="importer-postcode-lookup"),
]
