#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.decorators import method_decorator
from . import models, views
from viewflow.base import Flow, this
from viewflow import flow

__all__ = ['ApprovalRequestFlow']


def send_approval_request_email(activation):
    pass


def send_approval_request_response_email(activation):
    pass


class ApprovalRequestFlow(Flow):
    process_template = 'web/domains/case/access/partials/approval-request-display.html'
    process_class = models.ApprovalRequestProcess

    start = flow.StartSubprocess(func=this.start_func).Next(
        this.notify_contacts)

    notify_contacts = flow.Handler(send_approval_request_email).Next(
        this.respond)

    respond = flow.View(views.ApprovalRequestResponseView, ).Next(
        this.notify_case_officers).Assign(lambda activation: activation.process
                                          .approval_request.requested_from)

    notify_case_officers = flow.Handler(
        send_approval_request_response_email).Next(this.end)

    end = flow.End()

    @method_decorator(flow.flow_start_func)
    def start_func(self, activation, parent_task):
        activation.prepare(parent_task)
        activation.process.approval_request = parent_task.process.access_request.approval_requests.first(
        )
        activation.done()
        return activation
