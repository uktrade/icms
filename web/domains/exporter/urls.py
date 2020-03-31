#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('', views.ExporterListView.as_view(), name='exporter-list'),
    path('<int:pk>/edit/',
         views.ExporterEditView.as_view(),
         name='exporter-edit'),
    path('new/', views.ExporterCreateView.as_view(), name='exporter-new'),
    path('<int:pk>/', views.ExporterDetailView.as_view(),
         name='exporter-view'),
]
