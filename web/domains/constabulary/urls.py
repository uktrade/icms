#!/usr/bin/env python

from django.urls import path

from . import views as constabulary_views

urlpatterns = [
    path("", constabulary_views.ConstabularyListView.as_view(), name="constabulary-list"),
    path(
        "<int:pk>/", constabulary_views.ConstabularyDetailView.as_view(), name="constabulary-detail"
    ),
    path("new/", constabulary_views.ConstabularyCreateView.as_view(), name="constabulary-new"),
    path(
        "<int:pk>/edit/",
        constabulary_views.ConstabularyEditView.as_view(),
        name="constabulary-edit",
    ),
]
