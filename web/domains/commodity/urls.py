#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from . import views as commodity_views

urlpatterns = [
    # Commodity Management
    path('',
         commodity_views.CommodityListView.as_view(),
         name='commodity-list'),
    path('<int:pk>/',
         commodity_views.CommodityDetailView.as_view(),
         name='commodity-detail'),
    path('<int:pk>/edit/',
         commodity_views.CommodityEditView.as_view(),
         name='commodity-edit'),
    path('new/',
         commodity_views.CommodityCreateView.as_view(),
         name='commodity-new'),

    # Commodity Groups Management
    path('group/',
         commodity_views.CommodityGroupListView.as_view(),
         name='commodity-group-list'),
    path('group/<int:pk>/',
         commodity_views.CommodityGroupDetailView.as_view(),
         name='commodity-group-detail'),
    path('group/<int:pk>/edit/',
         commodity_views.CommodityGroupEditView.as_view(),
         name='commodity-group-edit'),
    path('group/new/',
         commodity_views.CommodityGroupCreateView.as_view(),
         name='commodity-group-new'),
]
