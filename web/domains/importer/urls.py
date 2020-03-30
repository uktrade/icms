#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('importer/', views.ImporterListView.as_view(), name='importer-list'),
    path('importer/<int:pk>/edit/',
         views.ImporterEditView.as_view(),
         name='importer-edit'),
    path('importer/new/',
         views.ImporterCreateView.as_view(),
         name='importer-new'),
    path('importer/<int:pk>/',
         views.ImporterDetailView.as_view(),
         name='importer-view'),

    # Importer Agents
    path('importer/<int:importer_id>/agent/<int:pk>/edit',
         views.ImporterEditView.as_view(),
         name='importer-agent-edit'),
    path('importer/<int:importer_id>/agent/new/',
         views.ImporterCreateView.as_view(),
         name='importer-agent-new'),
]
