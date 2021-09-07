import factory

from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSSchedule,
    ExportApplicationType,
)
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.user.factory import UserFactory


class CertificateOfManufactureApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfManufactureApplication

    process_type = CertificateOfManufactureApplication.PROCESS_TYPE

    application_type = factory.Iterator(ExportApplicationType.objects.filter(type_code="COM"))
    created_by = factory.SubFactory(UserFactory)
    exporter = factory.SubFactory(ExporterFactory)
    last_updated_by = factory.SubFactory(UserFactory)


class CertificateOfGMPApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfGoodManufacturingPracticeApplication

    process_type = CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE
    application_type = factory.Iterator(ExportApplicationType.objects.filter(type_code="GMP"))
    created_by = factory.SubFactory(UserFactory)
    exporter = factory.SubFactory(ExporterFactory)
    last_updated_by = factory.SubFactory(UserFactory)


class CertificateOfFreeSaleApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfFreeSaleApplication

    process_type = CertificateOfFreeSaleApplication.PROCESS_TYPE

    application_type = factory.Iterator(ExportApplicationType.objects.filter(type_code="CFS"))
    created_by = factory.SubFactory(UserFactory)
    exporter = factory.SubFactory(ExporterFactory)
    last_updated_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def schedules(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for schedule in extracted:
                self.schedules.add(schedule)


class CFSScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CFSSchedule

    created_by = factory.SubFactory(UserFactory)
