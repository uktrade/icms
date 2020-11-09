import factory
import factory.fuzzy
from django.utils import timezone
from viewflow.models import Task

from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


def is_importer_request(access_request):
    return access_request.request_type in [AccessRequest.IMPORTER, AccessRequest.IMPORTER_AGENT]


class AccessRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessRequest

    reference = "test"
    status = factory.fuzzy.FuzzyChoice(AccessRequest.STATUSES, getter=lambda s: s[0])
    organisation_name = factory.Faker("company")
    organisation_address = factory.Faker("address")
    request_reason = factory.Sequence(lambda n: f"reason {n}")
    agent_name = factory.Sequence(lambda n: f"agent name {n}")
    agent_address = factory.Sequence(lambda n: f"agent address {n}")
    submit_datetime = timezone.now()
    submitted_by = factory.SubFactory(UserFactory, is_active=True)
    last_update_datetime = timezone.now()
    submitted_by = factory.SubFactory(UserFactory, is_active=True)
    last_updated_by = factory.SubFactory(UserFactory, is_active=True)
    response_reason = ""


class ImporterAccessRequestFactory(AccessRequestFactory):
    class Meta:
        model = ImporterAccessRequest

    process_type = ImporterAccessRequest.PROCESS_TYPE
    link = factory.SubFactory(ImporterFactory)
    request_type = "MAIN_IMPORTER_ACCESS"


class ExporterAccessRequestFactory(AccessRequestFactory):
    class Meta:
        model = ExporterAccessRequest

    process_type = ExporterAccessRequest.PROCESS_TYPE
    link = factory.SubFactory(ExporterFactory)
    request_type = "MAIN_EXPORTER_ACCESS"


class ImporterAccessRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    process = factory.SubFactory(ImporterAccessRequestFactory)
    owner = None
    owner_permission = factory.LazyAttribute(lambda t: t.flow_task._owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        if self.owner:
            activation = self.activate()
            activation.assign(self.owner)


class ExporterAccessRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    process = factory.SubFactory(ExporterAccessRequestFactory)
    owner = None
    owner_permission = factory.LazyAttribute(lambda t: t.flow_task._owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        if self.owner:
            activation.assign(self.owner)
