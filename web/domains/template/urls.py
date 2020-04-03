#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from .views import TemplateListView, TemplateDetailView

urlpatterns = [
    path('', TemplateListView.as_view(), name='template-list'),
    path('<int:pk>', TemplateDetailView.as_view(), name='template-view'),
]
