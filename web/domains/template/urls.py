#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path

from .views import TemplateListView

urlpatterns = [
    path('template/', TemplateListView.as_view(), name='template-list'),
]
