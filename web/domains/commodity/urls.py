#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from . import views as commodity_views

urlpatterns = [
    # Commodity Management
    path('commodity/',
         commodity_views.CommodityListView.as_view(),
         name='commodity-list'),
    path('commodity/<int:pk>/',
         commodity_views.CommodityDetailView.as_view(),
         name='commodity-detail'),
    path('commodity/<int:pk>/edit/',
         commodity_views.CommodityEditView.as_view(),
         name='commodity-edit'),
    path('commodity/new/',
         commodity_views.CommodityCreateView.as_view(),
         name='commodity-new'),

    # Commodity Groups Management
    path('commodity/group/',
         commodity_views.CommodityGroupListView.as_view(),
         name='commodity-group-list'),
    path('commodity/group/<int:pk>/',
         commodity_views.CommodityGroupDetailView.as_view(),
         name='commodity-group-detail'),
    path('commodity/group/<int:pk>/edit/',
         commodity_views.CommodityGroupEditView.as_view(),
         name='commodity-group-edit'),
    path('commodity/group/new/',
         commodity_views.CommodityGroupCreateView.as_view(),
         name='commodity-group-new'),
]
