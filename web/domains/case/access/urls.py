#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.urls import include, path
from web.viewflow.viewset import FlowViewSet

from web.domains.case.fir.views import FurtherInformationRequestView
from web.flows import ImporterAccessRequestFlow, ExporterAccessRequestFlow, ApprovalRequestFlow

from . import views

logger = logging.getLogger(__name__)

importer_access_request_urls = FlowViewSet(ImporterAccessRequestFlow).urls
exporter_access_request_urls = FlowViewSet(ExporterAccessRequestFlow).urls
approval_request_urls = FlowViewSet(ApprovalRequestFlow).urls

app_name = "access"

urlpatterns = [
    path("<process_id>/fir/", FurtherInformationRequestView.as_view(), name="fir"),
    path("importer/", include((importer_access_request_urls, "importer"))),
    path("exporter/", include((exporter_access_request_urls, "exporter"))),
    path("approval/", include((approval_request_urls, "approval"))),
    path("requested/", views.AccessRequestCreatedView.as_view(), name="requested"),
]
