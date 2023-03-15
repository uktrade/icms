import factory.fuzzy
from django.utils import timezone

from web.models import AccessRequest, ExporterAccessRequest, ImporterAccessRequest
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


class AccessRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccessRequest

    status = AccessRequest.Statuses.SUBMITTED
    organisation_name = factory.Faker("company")
    organisation_address = factory.Faker("address")
    request_reason = factory.Sequence(lambda n: f"reason {n}")
    agent_name = factory.Sequence(lambda n: f"agent name {n}")
    agent_address = factory.Sequence(lambda n: f"agent address {n}")
    submit_datetime = timezone.now()
    submitted_by = factory.SubFactory(UserFactory, is_active=True)
    last_update_datetime = timezone.now()
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
