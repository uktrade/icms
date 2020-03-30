#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('import/apply/',
         views.ImportApplicationCreateView.as_view(),
         name='import_application_new'),
]
