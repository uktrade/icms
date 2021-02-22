import factory

from web.domains.case.export.models import (
    CertificateOfManufactureApplication,
    ExportApplicationType,
)
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.user.factory import UserFactory


class CertificateOfManufactureApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfManufactureApplication

    application_type = factory.Iterator(ExportApplicationType.objects.filter(type_code="COM"))
    created_by = factory.SubFactory(UserFactory)
    exporter = factory.SubFactory(ExporterFactory)
    last_updated_by = factory.SubFactory(UserFactory)
