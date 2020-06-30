#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from viewflow import flow
from viewflow.base import Flow, this

from web.notify import notify
from web.viewflow.nodes import View

from . import models, views
from .approval.flows import ApprovalRequestFlow

# Get an instance of a logger
logger = logging.getLogger(__name__)

__all__ = ['AccessRequestFlow']


def reset_re_link_flag(activation):
    process = activation.process
    process.re_link = False
    process.save()


def reset_restart_approval_flag(activation):
    process = activation.process
    process.restart_approval = False
    process.save()


def notify_officers(activation):
    notify.access_requested(activation.process.access_request)


def notify_access_request_closed(activation):
    notify.access_request_closed(activation.process.access_request)


def close_request(activation):
    activation.process.access_request.status = models.AccessRequest.CLOSED
    activation.process.access_request.save()


def case_officer_permission(activation):
    return 'IMP_CASE_OFFICER' if activation.process.access_request.is_importer(
    ) else 'IMP_CERT_CASE_OFFICER'


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

    notify_case_officers = flow.Handler(notify_officers).Next(this.review)

    review = View(views.AccessRequestReviewView).Next(
        this.check_approval_required).Permission(case_officer_permission)

    check_approval_required = flow.If(
        cond=lambda activation: activation.process.approval_required).Then(
            this.check_requester_type).Else(this.close_request)

    # resets re_link flag
    re_link = flow.Handler(reset_re_link_flag).Next(this.check_requester_type)

    check_requester_type = flow.If(this.is_importer).Then(
        this.link_importer).Else(this.link_exporter)

    link_importer = View(views.LinkImporterView).Next(
        this.request_approval).Permission(case_officer_permission).Assign(
            this.review.owner)

    link_exporter = View(views.LinkExporterView).Next(
        this.request_approval).Permission(case_officer_permission).Assign(
            this.review.owner)

    # resets restart_approval flag
    restart_approval = flow.Handler(reset_restart_approval_flag).Next(
        this.request_approval)

    request_approval = View(views.RequestApprovalView).Next(
        this.check_re_link_required).Permission(
            case_officer_permission).Assign(this.review.owner)

    check_re_link_required = flow.If(
        cond=lambda activation: activation.process.re_link).Then(
            this.re_link).Else(this.approval)

    approval = flow.Subprocess(ApprovalRequestFlow.start, ).Next(
        this.review_approval)

    review_approval = View(views.ApprovalRequestReviewView).Next(
        this.check_approval_restart).Permission(
            case_officer_permission).Assign(this.review.owner)

    check_approval_restart = flow.If(
        cond=lambda act: act.process.restart_approval).Then(
            this.restart_approval).Else(this.close_request)

    close_request = View(views.CloseAccessRequestView).Permission(
        case_officer_permission).Assign(this.review.owner).Next(
            this.email_requester)

    email_requester = flow.Handler(notify_access_request_closed).Next(this.end)

    end = flow.End()

    def is_importer(self, activation):
        return activation.process.access_request.is_importer()
