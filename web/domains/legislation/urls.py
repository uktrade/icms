#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('product-legislation/',
         views.ProductLegislationListView.as_view(),
         name='product-legislation-list'),
    path('product-legislation/new/',
         views.ProductLegislationCreateView.as_view(),
         name='product-legislation-new'),
    path('product-legislation/<int:pk>/',
         views.ProductLegislationDetailView.as_view(),
         name='product-legislation-detail'),
    path('product-legislation/<int:pk>/edit/',
         views.ProductLegislationUpdateView.as_view(),
         name='product-legislation-edit'),
]
