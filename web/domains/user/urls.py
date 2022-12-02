#!/usr/bin/env python
from django.urls import path

from .views import UsersListView, current_user_details, user_details

urlpatterns = [
    path("", current_user_details, name="current-user-details"),
    path("users/", UsersListView.as_view(), name="users-list"),
    path("users/<negint:pk>/", user_details, name="user-details"),
]
