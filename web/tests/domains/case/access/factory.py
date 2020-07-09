#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random

import factory
import factory.fuzzy
from django.utils import timezone
from viewflow.models import Task

from web.domains.case.access.flows import ExporterAccessRequestFlow, ImporterAccessRequestFlow
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequestProcess,
    ImporterAccessRequestProcess,
)
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


def is_importer_request(access_request):
    return access_request.request_type in [AccessRequest.IMPORTER, AccessRequest.IMPORTER_AGENT]


def is_agent_request(access_request):
    return access_request.request_type in [
        AccessRequest.IMPORTER_AGENT,
        AccessRequest.EXPORTER_AGENT,
    ]


def set_request_reason(access_request):
    """
        Request reason is only for importers and importer agents
    """
    if is_importer_request(access_request):
        return factory.Faker("sentence", nb_words=3)


def set_agent_name(access_request):
    """
        Agent name is only set if request is for agent
    """
    if is_agent_request(access_request):
        return factory.Faker("company")


def set_agent_address(access_request):
    """
        Agent name is only set if request is for agent
    """
    if is_agent_request(access_request):
        return factory.Faker("address")


class AccessRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessRequest

    reference = "test"
    request_type = factory.fuzzy.FuzzyChoice(AccessRequest.REQUEST_TYPES, getter=lambda t: t[0])
    status = factory.fuzzy.FuzzyChoice(AccessRequest.STATUSES, getter=lambda s: s[0])
    organisation_name = factory.Faker("company")
    organisation_address = factory.Faker("address")
    request_reason = factory.LazyAttribute(lambda a: set_request_reason(a))
    agent_name = factory.LazyAttribute(lambda a: set_agent_name(a))
    agent_address = factory.LazyAttribute(lambda a: set_agent_address(a))
    submit_datetime = timezone.now()
    submitted_by = factory.SubFactory(UserFactory, is_active=True)
    last_update_datetime = timezone.now()
    submitted_by = factory.SubFactory(UserFactory, is_active=True)
    last_updated_by = factory.SubFactory(UserFactory, is_active=True)
    closed_datetime = None
    closed_by = None
    response = None
    response_reason = None
    linked_importer = factory.SubFactory(ImporterFactory, is_active=True)
    linked_exporter = factory.SubFactory(ExporterFactory, is_active=True)


class ImporterAccessRequestProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImporterAccessRequestProcess

    access_request = factory.SubFactory(
        AccessRequestFactory,
        request_type=random.choices([AccessRequest.IMPORTER, AccessRequest.IMPORTER_AGENT]),
    )
    flow_class = ImporterAccessRequestFlow
    approval_required = False
    restart_approval = False
    re_link = False


class ExporterAccessRequestProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExporterAccessRequestProcess

    access_request = factory.SubFactory(
        AccessRequestFactory,
        request_type=random.choices([AccessRequest.EXPORTER, AccessRequest.EXPORTER_AGENT]),
    )
    flow_class = ExporterAccessRequestFlow
    approval_required = False
    restart_approval = False
    re_link = False


class ImporterAccessRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    process = factory.SubFactory(ImporterAccessRequestProcessFactory)
    flow_task = ImporterAccessRequestFlow.link_importer
    owner = None
    owner_permission = factory.LazyAttribute(lambda t: t.flow_task._owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        if self.owner:
            activation.assign(self.owner)


class ExporterAccessRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    process = factory.SubFactory(ExporterAccessRequestProcessFactory)
    flow_task = ExporterAccessRequestFlow.link_exporter
    owner = None
    owner_permission = factory.LazyAttribute(lambda t: t.flow_task._owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        if self.owner:
            activation.assign(self.owner)
