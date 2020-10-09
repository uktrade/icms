#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ExporterListView.as_view(), name="exporter-list"),
    path("<int:pk>/edit/", views.edit_exporter, name="exporter-edit"),
    path("create/", views.create_exporter, name="exporter-create"),
    path("<int:pk>/contacts/add/", views.add_contact, name="exporter-contact-add"),
    path(
        "<int:pk>/contacts/<int:contact_pk>/delete/",
        views.delete_contact,
        name="exporter-contact-delete",
    ),
]
