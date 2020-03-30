#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path,include

from viewflow.flow.viewset import FlowViewSet
from web.domains.workbasket.views import take_ownership
from web.flows import AccessRequestFlow

from . import views

access_request_urls = FlowViewSet(AccessRequestFlow).urls

urlpatterns = [
    path('access/<process_id>/fir',
         views.AccessRequestFirView.as_view(),
         name="access_request_fir_list"),
    path('access/', include(access_request_urls)),
    path('access/<process_id>/review_request/<task_id>/link-importer/',
         views.LinkImporterView.as_view(),
         name="link-importer"),
    path('access/<process_id>/review_request/<task_id>/link-exporter/',
         views.LinkExporterView.as_view(),
         name="link-exporter"),
    path("access-created/",
         views.AccessRequestCreatedView.as_view(),
         name="access_request_created"),
    path("take-ownership/<process_id>/", take_ownership,
         name="take_ownership"),
]
