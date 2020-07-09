#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views as auth_views

urlpatterns = [
    path("", auth_views.LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", auth_views.register, name="register"),
    path("reset-password/", auth_views.reset_password, name="reset-password"),
    path("set-password/", auth_views.set_password, name="set-password"),
    path("password/", auth_views.change_password, name="change-password"),
]
