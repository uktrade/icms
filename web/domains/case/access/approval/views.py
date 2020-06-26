#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect
from django.urls import reverse
from viewflow.flow.views import FlowMixin, UpdateProcessView

from web.views import ModelCreateView

from . import forms, models


class RequestApprovalView(FlowMixin, ModelCreateView):
    template_name = 'web/domains/case/access/request-approval.html'
    permission_required = []
    model = models.ApprovalRequest

    def get_form(self):
        access_request = self.activation.process.access_request
        team = access_request.linked_importer or access_request.linked_exporter
        return forms.ApprovalRequestForm(team, data=self.request.POST or None)

    def form_valid(self, form):
        """
            Save approval request
        """
        process = self.activation.process
        process.save()
        access_request = process.access_request
        approval_request = form.instance
        approval_request.access_request = access_request
        approval_request.requested_by = self.request.user
        return super().form_valid(form)

    def _re_link(self):
        process = self.activation.process
        process.re_link = True
        process.save()
        self.activation.done()
        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        if '_re_link' in request.POST:
            return self._re_link()
        return super().post(request, *args, **kwargs)


class ApprovalRequestResponseView(UpdateProcessView):
    template_name = 'web/domains/case/access/approval/respond.html'
    form_class = forms.ApprovalRequestResponseForm

    def post(self, request, *args, **kwargs):
        approval_request = self.activation.process.approval_request
        approval_request.status = models.ApprovalRequest.COMPLETED
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('workbasket')


class ApprovalRequestReviewView(UpdateProcessView):
    template_name = 'web/domains/case/access/review-approval.html'

    def get_approval_process(self):
        """
            Retrieves the approval process to be reviewed
        """
        process = self.activation.process
        flow_class = self.activation.flow_class
        flow_task = flow_class.approval
        approval_task = flow_class.task_class._default_manager.filter(
            process=process, flow_task=flow_task).order_by('-created').first()
        return approval_task.activate().subprocesses().first()

    def get_context_data(self, *args, **kwargs):
        """
            Adds latest approval process into context
        """
        context = super().get_context_data(*args, **kwargs)
        context['approval_process'] = self.get_approval_process()
        return context

    def post(self, request, *args, **kwargs):
        process = self.activation.process
        if 'start_approval' in request.POST:
            process.restart_approval = True
        process.save()
        return super().post(request, *args, **kwargs)
