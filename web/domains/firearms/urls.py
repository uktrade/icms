#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('obsolete-calibre/',
         views.ObsoleteCalibreListView.as_view(),
         name='obsolete-calibre-list'),
    path('obsolete-calibre/new',
         views.ObsoleteCalibreGroupCreateView.as_view(),
         name='obsolete-calibre-new'),
    path('obsolete-calibre/<int:pk>/edit/',
         views.ObsoleteCalibreGroupEditView.as_view(),
         name='obsolete-calibre-edit'),
    path('obsolete-calibre/<int:pk>/',
         views.ObsoleteCalibreGroupDetailView.as_view(),
         name='obsolete-calibre-view'),
]
