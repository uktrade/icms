#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    # Countries management
    path("", views.CountryListView.as_view(), name="country-list"),
    path("new/", views.CountryCreateView.as_view(), name="country-new"),
    path("<int:pk>/edit/", views.CountryEditView.as_view(), name="country-edit"),
    # Country Groups Management
    path("groups/", views.CountryGroupView.as_view(), name="country-group-view"),
    path("groups/<int:pk>/", views.CountryGroupView.as_view(), name="country-group-view"),
    path("groups/new/", views.CountryGroupCreateView.as_view(), name="country-group-new"),
    path("groups/<int:pk>/edit/", views.CountryGroupEditView.as_view(), name="country-group-edit"),
    # Coutry translation sets
    path(
        "translations/",
        views.CountryTranslationSetListView.as_view(),
        name="country-translation-set-list",
    ),
    path(
        "translations/<int:pk>/edit/",
        views.CountryTranslationSetEditView.as_view(),
        name="country-translation-set-edit",
    ),
    path(
        "translations/<int:set_pk>/edit/<int:country_pk>/",
        views.CountryTranslationCreateUpdateView.as_view(),
        name="country-translation-edit",
    ),
]
