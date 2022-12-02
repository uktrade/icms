#!/usr/bin/env python

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProductLegislationListView.as_view(), name="product-legislation-list"),
    path("new/", views.ProductLegislationCreateView.as_view(), name="product-legislation-new"),
    path(
        "<int:pk>/", views.ProductLegislationDetailView.as_view(), name="product-legislation-detail"
    ),
    path(
        "<int:pk>/edit/",
        views.ProductLegislationUpdateView.as_view(),
        name="product-legislation-edit",
    ),
]
