#!/usr/bin/env python
# -*- coding: utf-8 -*-

import factory
from django.utils import timezone
from viewflow.models import Task

from web.domains.case.access.approval.flows import ApprovalRequestFlow
from web.domains.case.access.approval.models import ApprovalRequest, ApprovalRequestProcess
from web.tests.domains.case.access.factory import AccessRequestFactory
from web.tests.domains.user.factory import UserFactory


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalRequest

    access_request = factory.SubFactory(AccessRequestFactory)

    status = factory.fuzzy.FuzzyChoice(ApprovalRequest.STATUSES, getter=lambda s: s[0])
    request_date = timezone.now()
    requested_by = factory.SubFactory(UserFactory, is_active=True)
    requested_from = None
    response = None
    response_by = None
    response_date = None
    response_reason = None


class ApprovalRequestProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalRequestProcess

    approval_request = factory.SubFactory(ApprovalRequestFactory)
    flow_class = ApprovalRequestFlow


class ApprovalRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    process = factory.SubFactory(ApprovalRequestProcessFactory)
    flow_task = ApprovalRequestFlow.respond
    owner = None
    owner_permission = factory.LazyAttribute(lambda t: t.flow_task._owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        if self.owner:
            activation.assign(self.owner)
