#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ExporterListView.as_view(), name="exporter-list"),
    path("<int:pk>/edit/", views.edit_exporter, name="exporter-edit"),
    path("create/", views.create_exporter, name="exporter-create"),
    # contacts
    path("<int:pk>/contacts/add/", views.add_contact, name="exporter-contact-add"),
    path(
        "<int:pk>/contacts/<int:contact_pk>/delete/",
        views.delete_contact,
        name="exporter-contact-delete",
    ),
    # offices
    path("<int:pk>/offices/create/", views.create_office, name="exporter-office-create"),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/edit/",
        views.edit_office,
        name="exporter-office-edit",
    ),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/archive/",
        views.archive_office,
        name="exporter-office-archive",
    ),
    path(
        "<int:exporter_pk>/offices/<int:office_pk>/unarchive/",
        views.unarchive_office,
        name="exporter-office-unarchive",
    ),
]
