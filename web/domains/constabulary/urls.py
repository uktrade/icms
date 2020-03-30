#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views as constabulary_views

urlpatterns = [
    path('constabulary/',
         constabulary_views.ConstabularyListView.as_view(),
         name='constabulary-list'),
    path('constabulary/<int:pk>/',
         constabulary_views.ConstabularyDetailView.as_view(),
         name='constabulary-detail'),
    path('constabulary/new/',
         constabulary_views.ConstabularyCreateView.as_view(),
         name='constabulary-new'),
    path('constabulary/<int:pk>/edit/',
         constabulary_views.ConstabularyEditView.as_view(),
         name='constabulary-edit'),
]
