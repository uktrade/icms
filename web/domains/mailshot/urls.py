#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path('', views.MailshotListView.as_view(), name='mailshot-list'),
    path('new/', views.MailshotCreateView.as_view(), name='mailshot-new'),
    path('<int:pk>/',
         views.MailshotDetailView.as_view(),
         name='mailshot-detail'),
    path('<int:pk>/edit/',
         views.MailshotEditView.as_view(),
         name='mailshot-edit'),
    path('<int:pk>/retract/',
         views.MailshotRetractView.as_view(),
         name='mailshot-retract'),
    path('received/',
         views.ReceivedMailshotsView.as_view(),
         name='mailshot-received'),
    path('received/<int:pk>/',
         views.MailshotDetailView.as_view(
             cancel_url=reverse_lazy('mailshot-received')),
         name='mailshot-detail-received'),
]
