#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.utils.decorators import method_decorator
from viewflow import flow
from viewflow.base import Flow, this

from web.domains import User
from web.notify import notify

from . import models, views

# Get an instance of a logger
logger = logging.getLogger(__name__)

__all__ = ['AccessRequestFlow', 'ApprovalRequestFlow']


def send_admin_notification_email(activation):
    ilb_admins = User.objects.filter(is_staff=True)
    for admin in ilb_admins:
        try:
            notify.access_request_admin(admin,
                                        activation.process.access_request)
        except Exception as e:  # noqa
            logger.exception('Failed to notify an ILB admin', e)


def send_requester_notification_email(activation):
    notify.access_request_requester(activation.process.access_request)


def send_approval_request_email(activation):
    pass


def send_approval_request_response_email(activation):
    pass


def close_request(activation):
    activation.process.access_request.status = models.AccessRequest.CLOSED
    activation.process.access_request.save()


def has_approval(activation):
    """
    Check if access_request has an approval process
    """
    access_request = activation.process.access_request
    return hasattr(
        access_request,
        'approval_request') and not access_request.approval_request.is_complete


class ApprovalRequestFlow(Flow):
    process_class = models.ApprovalRequestProcess

    start = flow.StartSubprocess(func=this.start_func).Next(
        this.notify_contacts)

    notify_contacts = flow.Handler(send_approval_request_email).Next(
        this.respond)

    respond = flow.View(views.ApprovalRequestResponseView).Next(
        this.notify_case_officers).Assign(lambda activation: activation.process
                                          .approval_request.requested_from)

    notify_case_officers = flow.Handler(
        send_approval_request_response_email).Next(this.end)

    end = flow.End()

    @method_decorator(flow.flow_start_func)
    def start_func(self, activation, parent_task):
        activation.prepare(parent_task)
        activation.process.approval_request = parent_task.process.access_request.approval_request
        activation.done()
        return activation


class AccessRequestFlow(Flow):
    process_class = models.AccessRequestProcess

    request = flow.Start(views.AccessRequestCreateView).Next(
        this.notify_case_officers)

    notify_case_officers = flow.Handler(send_admin_notification_email).Next(
        this.review)

    review = flow.View(
        views.AccessRequestReviewView,
        assign_view=views.AccessRequestTakeOwnershipView.as_view()).Next(
            this.check_approval_required)

    check_approval_required = flow.If(
        cond=lambda act: act.process.approval_required).Then(
            this.check_requester_type).Else(this.close_request)

    check_requester_type = flow.If(this.is_importer).Then(
        this.link_importer).Else(this.link_exporter)

    link_importer = flow.View(views.LinkImporterView).Next(
        this.request_approval).Assign(this.review.owner)

    link_exporter = flow.View(views.LinkExporterView).Next(
        this.request_approval).Assign(this.review.owner)

    request_approval = flow.View(views.RequestApprovalView).Next(
        this.start_approval).Assign(this.review.owner)

    start_approval = flow.Subprocess(ApprovalRequestFlow.start).Next(
        this.review)

    close_request = flow.View(views.CloseAccessRequestView).Assign(
        this.review.owner).Next(this.email_requester)

    email_requester = flow.Handler(send_requester_notification_email).Next(
        this.end)

    end = flow.End()

    def is_importer(self, activation):
        return activation.process.access_request.requester_type == 'importer'
