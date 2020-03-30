#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('workbasket/', views.workbasket, name='workbasket'),
]
