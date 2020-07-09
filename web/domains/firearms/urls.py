#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ObsoleteCalibreListView.as_view(), name="obsolete-calibre-list"),
    path("new", views.ObsoleteCalibreGroupCreateView.as_view(), name="obsolete-calibre-new"),
    path(
        "<int:pk>/edit/", views.ObsoleteCalibreGroupEditView.as_view(), name="obsolete-calibre-edit"
    ),
    path("<int:pk>/", views.ObsoleteCalibreGroupDetailView.as_view(), name="obsolete-calibre-view"),
]
