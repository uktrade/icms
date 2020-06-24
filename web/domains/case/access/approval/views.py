#!/usr/bin/env python
# -*- coding: utf-8 -*-

from viewflow.flow.views import (CancelProcessView, FlowMixin,
                                 UpdateProcessView)
from web.views import ModelCreateView

from . import forms, models

from django.urls import reverse
from viewflow.activation import STATUS


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
        process.restart_approval = False  # Reset approval_restart flag
        process.save()
        access_request = process.access_request
        approval_request = form.instance
        approval_request.access_request = access_request
        approval_request.requested_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workbasket')


class ApprovalRequestResponseView(UpdateProcessView):
    template_name = 'web/domains/case/access/approval/respond.html'
    form_class = forms.ApprovalRequestResponseForm

    def post(self, request, *args, **kwargs):
        approval_request = self.activation.process.approval_request
        approval_request.status = models.ApprovalRequest.COMPLETED
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('workbasket')


class ApprovalRequestWithdrawView(CancelProcessView):
    def unassign_tasks(self, tasks):
        """
            Unassign all approval request tasks and hand cancel process to Viewflow.

        """
        for task in tasks:
            activation = task.activate()
            if task.status == STATUS.ASSIGNED:
                activation.unassign()

    def finish_approval(self):
        """
            Finish approval parent task when subprocess in cancelled
        """
        approval_task = self.approval_process.parent_task
        activation = approval_task.activate()
        activation.done()

    def get_success_url(self):
        from .flows import AccessRequestFlow
        next_task = self.object.parent_task.process.task_set.filter(
            flow_task=AccessRequestFlow.review_approval).first()
        return next_task.flow_task.get_task_url(next_task,
                                                user=self.request.user,
                                                namespace='access')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.approval_process = self.object
        approval_request = self.approval_process.approval_request
        active_tasks = super()._get_task_list()

        # Viewflow doesn't allow cancelling unless all
        # process tasks are unassigned
        self.unassign_tasks(active_tasks)
        self.finish_approval()
        approval_request.status = models.ApprovalRequest.CANCELLED
        approval_request.save()

        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
            Withdraw view doesn't implement a page view.
            Form is to be posted from Access Request approval task
            detail view.
        """
        raise NotImplementedError


class ApprovalRequestReviewView(UpdateProcessView):
    template_name = 'web/domains/case/access/review-approval.html'

    def post(self, request, *args, **kwargs):
        process = self.activation.process
        if 'start_approval' in request.POST:
            process.restart_approval = True
        process.save()
        return super().post(request, *args, **kwargs)
