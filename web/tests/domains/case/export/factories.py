import factory

from web.domains.case.export.models import (
    CertificateOfManufactureApplication,
    ExportApplicationType,
)
from web.tests.domains.country.factory import CountryFactory, CountryGroupFactory
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.user.factory import UserFactory


class ExportApplicationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExportApplicationType

    is_active = True
    type_code = "COM"
    type = "Certificate of Manufacture"
    allow_multiple_products = False
    generate_cover_letter = False
    allow_hse_authorization = False
    country_group = factory.SubFactory(CountryGroupFactory)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            return
        self.country_group.countries.add(CountryFactory.create(is_active=True))


class CertificateOfManufactureApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfManufactureApplication

    application_type = factory.SubFactory(ExportApplicationTypeFactory)
    created_by = factory.SubFactory(UserFactory)
    exporter = factory.SubFactory(ExporterFactory)
    last_updated_by = factory.SubFactory(UserFactory)
