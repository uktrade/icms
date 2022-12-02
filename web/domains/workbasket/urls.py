#!/usr/bin/env python

from django.urls import path

from . import views

urlpatterns = [
    path("", views.show_workbasket, name="workbasket"),
]
