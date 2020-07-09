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

__all__ = ["ImporterAccessRequestFlow", "ExporterAccessRequestFlow"]

IMP_CASE_OFFICER = "web.IMP_CASE_OFFICER"
IMP_CERT_CASE_OFFICER = "web.IMP_CERT_CASE_OFFICER"


def notify_officers(activation):
    notify.access_requested(activation.process.access_request)


def notify_access_request_closed(activation):
    notify.access_request_closed(activation.process.access_request)


def assign_link_task(activation):
    """
        Assign "link_importer" & "link_exporter" tasks' owner
        to "review" task owner if importer relink action is taken at review task
    """
    task = activation.task
    process = activation.task.process
    previous = task.previous.first()
    if previous.flow_task.name == "check_re_link_required":
        # reset re_link flag
        process.re_link = False
        process.save()
        review_task = previous.previous.first()
        activation.assign(review_task.owner)
        activation.prepare()


def assign_review_task(activation):
    """
        Assign "review" task's owner
        to "close_request" task owner if
        restart approval action is taken at close request task
    """
    task = activation.task
    process = activation.task.process
    previous = task.previous.first()
    if previous.flow_task.name == "check_approval_restart":
        # reset approval restart flag
        process.restart_approval = False
        process.save()
        close_task = previous.previous.first()
        activation.assign(close_task.owner)
        activation.prepare()
    else:
        activation.assign(previous.owner)
        activation.prepare()


class ImporterAccessRequestFlow(Flow):
    process_template = "web/domains/case/access/partials/access-request-display.html"
    process_class = models.ImporterAccessRequestProcess

    # Performed by importers or their agents
    request = flow.Start(views.ImporterAccessRequestCreateView).Next(this.notify_case_officers)

    notify_case_officers = flow.Handler(notify_officers).Next(this.link_importer)

    # Performed by case officers
    # point of return if relink importer action is taken on review
    link_importer = (
        View(views.LinkImporterView)
        .Permission(IMP_CASE_OFFICER)
        .Next(this.review)
        .onCreate(assign_link_task)
    )

    # point to return if restart approval action is taken on close request
    review = (
        View(views.AccessRequestReviewView)
        .Next(this.check_re_link_required)
        .Permission(IMP_CASE_OFFICER)
        .onCreate(assign_review_task)
    )

    check_re_link_required = (
        flow.If(cond=lambda activation: activation.process.re_link)
        .Then(this.link_importer)
        .Else(this.check_approval_required)
    )

    check_approval_required = (
        flow.If(cond=lambda activation: activation.process.approval_required)
        .Then(this.approval)
        .Else(this.close_request)
    )

    approval = flow.Subprocess(ApprovalRequestFlow.start,).Next(this.close_request)

    close_request = (
        View(views.CloseAccessRequestView)
        .Permission(IMP_CASE_OFFICER)
        .Assign(this.review.owner)
        .Next(this.check_approval_restart)
    )

    check_approval_restart = (
        flow.If(cond=lambda act: act.process.restart_approval)
        .Then(this.review)
        .Else(this.email_requester)
    )

    email_requester = flow.Handler(notify_access_request_closed).Next(this.end)

    end = flow.End()


class ExporterAccessRequestFlow(Flow):
    process_template = "web/domains/case/access/partials/access-request-display.html"
    process_class = models.ExporterAccessRequestProcess

    # Performed by exporters or their agents
    request = flow.Start(views.ExporterAccessRequestCreateView).Next(this.notify_case_officers)

    notify_case_officers = flow.Handler(notify_officers).Next(this.link_exporter)

    # Performed by case officers

    # point to return if re link action taken on review
    link_exporter = (
        View(views.LinkExporterView)
        .Next(this.review)
        .Permission(IMP_CERT_CASE_OFFICER)
        .onCreate(assign_link_task)
    )

    # point to return if restart approval action is taken on close request task
    review = (
        View(views.AccessRequestReviewView)
        .Next(this.check_re_link_required)
        .Permission(IMP_CERT_CASE_OFFICER)
        .onCreate(assign_review_task)
    )

    check_re_link_required = (
        flow.If(cond=lambda activation: activation.process.re_link)
        .Then(this.link_exporter)
        .Else(this.check_approval_required)
    )

    check_approval_required = (
        flow.If(cond=lambda activation: activation.process.approval_required)
        .Then(this.approval)
        .Else(this.close_request)
    )

    approval = flow.Subprocess(ApprovalRequestFlow.start,).Next(this.close_request)

    close_request = (
        View(views.CloseAccessRequestView)
        .Permission(IMP_CERT_CASE_OFFICER)
        .Assign(this.review.owner)
        .Next(this.check_approval_restart)
    )

    check_approval_restart = (
        flow.If(cond=lambda act: act.process.restart_approval)
        .Then(this.review)
        .Else(this.email_requester)
    )

    email_requester = flow.Handler(notify_access_request_closed).Next(this.end)

    end = flow.End()
