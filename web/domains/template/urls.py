#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from .views import TemplateListView, TemplateDetailView, TemplateEditView

urlpatterns = [
    path('', TemplateListView.as_view(), name='template-list'),
    path('<int:pk>', TemplateDetailView.as_view(), name='template-view'),
    path('<int:pk>/edit/', TemplateEditView.as_view(), name='template-edit'),
]
