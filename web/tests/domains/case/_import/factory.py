import factory.fuzzy

from web.models import (
    ImportApplicationType,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
)


class OILApplicationFactory(factory.django.DjangoModelFactory):
    process_type = OpenIndividualLicenceApplication.PROCESS_TYPE
    application_type = factory.Iterator(
        ImportApplicationType.objects.filter(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.OIL
        )
    )

    class Meta:
        model = OpenIndividualLicenceApplication


class SanctionsAndAdhocLicenseApplicationFactory(factory.django.DjangoModelFactory):
    process_type = SanctionsAndAdhocApplication.PROCESS_TYPE
    application_type = factory.Iterator(
        ImportApplicationType.objects.filter(type=ImportApplicationType.Types.SANCTION_ADHOC)
    )

    class Meta:
        model = SanctionsAndAdhocApplication


class SanctionsAndAdhocApplicationGoodsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SanctionsAndAdhocApplicationGoods
