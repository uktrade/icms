#!/usr/bin/env python
# -*- coding: utf-8 -*-

from viewflow.flow.viewset import FlowViewSet as ViewflowFlowViewSet
from .views import CancelProcessView


class FlowViewSet(ViewflowFlowViewSet):
    def __init__(self, flow_class):
        super().__init__(flow_class)
        # Use custom cancel process view
        self.cancel_process_view[1] = CancelProcessView.as_view()
