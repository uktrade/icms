#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import reverse
from viewflow.flow.views import UpdateProcessView

from . import forms, models


class ApprovalRequestResponseView(UpdateProcessView):
    template_name = 'web/domains/case/access/approval/respond.html'
    form_class = forms.ApprovalRequestResponseForm

    def post(self, request, *args, **kwargs):
        approval_request = self.activation.process.approval_request
        approval_request.status = models.ApprovalRequest.COMPLETED
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('workbasket')
