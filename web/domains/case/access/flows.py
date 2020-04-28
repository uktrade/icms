#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.utils.decorators import method_decorator
from viewflow import flow
from viewflow.base import Flow, this

from web.domains import User
from web.notify import notify

from .models import AccessRequest, AccessRequestProcess, ApprovalRequestProcess
from .views import AccessRequestCreateView, ILBReviewRequest

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


def close_request(activation):
    activation.process.access_request.status = AccessRequest.CLOSED
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
    process_class = ApprovalRequestProcess

    start = flow.StartSubprocess(func=this.start_func).Next(this.end)

    end = flow.End()

    @method_decorator(flow.flow_start_func)
    def start_func(self, activation, parent_task):
        activation.prepare(parent_task)
        activation.process.approval_request = parent_task.process.access_request.approval_request
        activation.done()
        return activation


class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess

    access_start = flow.Start(AccessRequestCreateView).Next(this.email_admins)

    email_admins = flow.Handler(send_admin_notification_email).Next(
        this.review_request)

    review_request = flow.View(ILBReviewRequest, ).Next(this.check_approval)

    # If an approval request is created start subprocess for approval
    check_approval = flow.If(cond=lambda act: has_approval(act)).Then(
        this.request_approval).Else(this.email_requester)

    request_approval = flow.Subprocess(ApprovalRequestFlow.start).Next(
        this.review_request)

    email_requester = (flow.Handler(send_requester_notification_email).Next(
        this.close_request))

    close_request = (flow.Handler(close_request).Next(this.end))

    end = flow.End()
