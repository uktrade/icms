#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from .views import (
    EndorsementCreateView,
    TemplateDetailView,
    TemplateEditView,
    TemplateListView,
    archive_endorsement_usage_link,
    edit_endorsement_usage,
    list_endorsement_usages,
)

urlpatterns = [
    path("", TemplateListView.as_view(), name="template-list"),
    path("<int:pk>/", TemplateDetailView.as_view(), name="template-view"),
    path("<int:pk>/edit/", TemplateEditView.as_view(), name="template-edit"),
    path("endorsement/new/", EndorsementCreateView.as_view(), name="template-endorsement-new"),
    path("endorsement/usages/", list_endorsement_usages, name="template-endorsement-usages"),
    path(
        "endorsement/usages/<int:pk>/edit/",
        edit_endorsement_usage,
        name="template-endorsement-usage-edit",
    ),
    path(
        "endorsement/usages/<int:usage_pk>link/<int:link_pk>/archive/",
        archive_endorsement_usage_link,
        name="template-endorsement-usage-link-archive",
    ),
]
