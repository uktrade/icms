#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from viewflow import flow
from viewflow.base import Flow, this

from web.domains import User
from web.notify import notify

from . import models, views

from .approval.flows import ApprovalRequestFlow
from .approval import views as approval_views

# Get an instance of a logger
logger = logging.getLogger(__name__)

__all__ = ['AccessRequestFlow']


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


class AccessRequestFlow(Flow):
    process_template = "web/domains/case/access/partials/access-request-display.html"
    process_class = models.AccessRequestProcess

    request = flow.Start(views.AccessRequestCreateView).Next(
        this.notify_case_officers)

    notify_case_officers = flow.Handler(send_admin_notification_email).Next(
        this.review)

    review = flow.View(views.AccessRequestReviewView).Next(
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

    request_approval = flow.View(approval_views.RequestApprovalView).Next(
        this.approval).Assign(this.review.owner)

    approval = flow.Subprocess(ApprovalRequestFlow.start).Next(
        this.review_approval)

    review_approval = flow.View(approval_views.ApprovalRequestReviewView).Next(
        this.check_approval_restart).Assign(this.review.owner)

    check_approval_restart = flow.If(
        cond=lambda act: act.process.restart_approval).Then(
            this.request_approval).Else(this.close_request)

    close_request = flow.View(views.CloseAccessRequestView).Assign(
        this.review.owner).Next(this.email_requester)

    email_requester = flow.Handler(send_requester_notification_email).Next(
        this.end)

    end = flow.End()

    def is_importer(self, activation):
        return activation.process.access_request.requester_type == 'importer'
