#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    # Exporter
    path('exporter/', views.ExporterListView.as_view(), name='exporter-list'),
    path('exporter/<int:pk>/edit/',
         views.ExporterEditView.as_view(),
         name='exporter-edit'),
    path('exporter/new/', views.ExporterCreateView.as_view(), name='exporter-new'),
    path('exporter/<int:pk>/',
         views.ExporterDetailView.as_view(),
         name='exporter-view'),
]
