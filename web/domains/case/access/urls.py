#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.urls import include, path
from viewflow.flow.viewset import FlowViewSet

from web.domains.case.fir.views import FurtherInformationRequestView
from web.flows import AccessRequestFlow, ApprovalRequestFlow

from . import views
from .approval import views as approval_views

logger = logging.getLogger(__name__)

access_request_urls = FlowViewSet(AccessRequestFlow).urls
approval_request_viewset = FlowViewSet(ApprovalRequestFlow)
# Override default cancel view
approval_request_viewset.cancel_process_view[
    1] = approval_views.ApprovalRequestWithdrawView.as_view()
approval_request_urls = approval_request_viewset.urls

app_name = 'access'

urlpatterns = [
    path('<process_id>/fir/',
         FurtherInformationRequestView.as_view(),
         name="fir"),
    path('', include(access_request_urls)),
    path('approval/', include((approval_request_urls, 'approval'))),
    path('<process_id>/review/<task_id>/link-importer/',
         views.LinkImporterView.as_view(),
         name="link-importer"),
    path('<process_id>/review/<task_id>/link-exporter/',
         views.LinkExporterView.as_view(),
         name="link-exporter"),
    path("requested/",
         views.AccessRequestCreatedView.as_view(),
         name="requested")
]
