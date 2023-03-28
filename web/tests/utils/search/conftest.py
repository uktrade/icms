import datetime
from typing import Any, NamedTuple

import pytest

from web.domains.case._import.opt.models import CP_CATEGORIES
from web.domains.case.models import DocumentPackBase
from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import submit_application
from web.flow.models import ProcessTypes
from web.middleware.common import ICMSMiddlewareContext
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSSchedule,
    Commodity,
    CommodityGroup,
    CommodityType,
    Country,
    DerogationsApplication,
    DFLApplication,
    ExportApplicationType,
    Exporter,
    ImportApplicationType,
    Importer,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    SILApplication,
    Task,
    TextilesApplication,
    User,
    WoodQuotaApplication,
)
from web.models.shared import FirearmCommodity
from web.types import AuthenticatedHttpRequest


class FixtureData(NamedTuple):
    importer: Importer
    agent_importer: Importer
    importer_user: User
    request: AuthenticatedHttpRequest


@pytest.fixture
def import_fixture_data(db, importer, agent_importer, test_import_user, request):
    request.user = test_import_user
    request.icms = ICMSMiddlewareContext()

    return FixtureData(importer, agent_importer, test_import_user, request)


class ExportFixtureData(NamedTuple):
    exporter: Exporter
    agent_exporter: Exporter
    exporter_user: User
    request: AuthenticatedHttpRequest


@pytest.fixture
def export_fixture_data(db, exporter, agent_exporter, test_export_user, request):
    request.user = test_export_user
    request.icms = ICMSMiddlewareContext()

    return ExportFixtureData(exporter, agent_exporter, test_export_user, request)


class Build:
    @staticmethod
    def derogation_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Tanzania",
        consignment_country="Algeria",
        commodity_code="code112233",
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.DEROGATION
        )
        process_type = ProcessTypes.DEROGATIONS
        commodity = create_test_commodity(commodity_code)

        derogation_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "commodity": commodity,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=derogation_kwargs,
        )

    @staticmethod
    def fa_dfl_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="the Czech Republic",
        consignment_country="the Slovak Republic",
        commodity_code=FirearmCommodity.EX_CHAPTER_97,
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
        )
        process_type = ProcessTypes.FA_DFL

        fa_dfl_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "commodity_code": commodity_code,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=fa_dfl_kwargs,
        )

    @staticmethod
    def fa_oil_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Any Country",
        consignment_country="Any Country",
        commodity_code=FirearmCommodity.EX_CHAPTER_93,
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.OIL
        )
        process_type = ProcessTypes.FA_OIL
        fa_oil_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "commodity_code": commodity_code,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=fa_oil_kwargs,
        )

    @staticmethod
    def fa_sil_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Argentina",
        consignment_country="Azerbaijan",
        commodity_code=FirearmCommodity.EX_CHAPTER_97,
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.SIL
        )
        process_type = ProcessTypes.FA_SIL
        fa_sil_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "commodity_code": commodity_code,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=fa_sil_kwargs,
        )

    @staticmethod
    def ironsteel_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Kazakhstan",
        consignment_country="Bahamas",
        shipping_year=2021,
        category_commodity_group="SA1",
        commodity_code="7208370010",
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.IRON_STEEL
        )
        process_type = ProcessTypes.IRON_STEEL
        commodity = create_test_commodity(commodity_code)
        commodity_group = create_test_commodity_group(category_commodity_group, commodity)

        ironsteel_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "shipping_year": shipping_year,
            "commodity": commodity,
            "category_commodity_group": commodity_group,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=ironsteel_kwargs,
        )

    @staticmethod
    def opt_application(
        reference,
        import_fixture_data: FixtureData,
        origin_country="Uruguay",
        consignment_country="USA",
        cp_category=CP_CATEGORIES[0],
        cp_commodity_codes=("6205200010", "6205908010"),
        teg_commodity_codes=("5006009000", "5007206190", "5112301000"),
    ):
        application_type = ImportApplicationType.objects.get(type=ImportApplicationType.Types.OPT)
        process_type = ProcessTypes.OPT
        cp_commodities = []
        teg_commodities = []

        for cc in cp_commodity_codes:
            cp_commodities.append(create_test_commodity(cc))

        for cc in teg_commodity_codes:
            teg_commodities.append(create_test_commodity(cc))

        opt_kwargs = {
            "cp_origin_country": Country.objects.get(name=origin_country),
            "cp_processing_country": Country.objects.get(name=consignment_country),
            "cp_category": cp_category,
        }

        application: OutwardProcessingTradeApplication = _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit=False,
            extra_kwargs=opt_kwargs,
        )

        for com in cp_commodities:
            application.cp_commodities.add(com)

        for com in teg_commodities:
            application.teg_commodities.add(com)

        _submit_application(application, import_fixture_data)

        return application

    @staticmethod
    def sanctionadhoc_application(
        reference,
        import_fixture_data: FixtureData,
        origin_country="Iran",
        consignment_country="Algeria",
        commodity_codes=("2801000010", "2850002070"),
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.SANCTION_ADHOC
        )
        process_type = ProcessTypes.SANCTIONS

        sanctionadhoc_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
        }

        application = _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit=False,
            extra_kwargs=sanctionadhoc_kwargs,
        )

        for com in commodity_codes:
            SanctionsAndAdhocApplicationGoods.objects.create(
                import_application=application,
                commodity=create_test_commodity(com),
                goods_description=f"Some goods: {com}",
                quantity_amount=123,
                value=123,
            )

        _submit_application(application, import_fixture_data)

        return application

    @staticmethod
    def sps_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Azerbaijan",
        consignment_country="Jordan",
        commodity_code="7208539000",
    ):
        application_type = ImportApplicationType.objects.get(type=ImportApplicationType.Types.SPS)
        process_type = ProcessTypes.SPS

        sps_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "commodity": create_test_commodity(commodity_code),
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=sps_kwargs,
        )

    @staticmethod
    def textiles_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        origin_country="Belarus",
        consignment_country="Argentina",
        shipping_year=2024,
        category_commodity_group="22",
        commodity_code="5509620000",
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.TEXTILES
        )
        process_type = ProcessTypes.TEXTILES

        commodity = create_test_commodity(commodity_code)
        commodity_group = create_test_commodity_group(category_commodity_group, commodity)

        textiles_kwargs = {
            "origin_country": Country.objects.get(name=origin_country),
            "consignment_country": Country.objects.get(name=consignment_country),
            "shipping_year": shipping_year,
            "commodity": commodity,
            "category_commodity_group": commodity_group,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            extra_kwargs=textiles_kwargs,
        )

    @staticmethod
    def wood_application(
        reference,
        import_fixture_data: FixtureData,
        submit=True,
        shipping_year=2021,
        commodity_code="1234567890",
        override_status=None,
    ):
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        )
        process_type = ProcessTypes.WOOD
        commodity = create_test_commodity(commodity_code)

        wood_kwargs = {
            "shipping_year": shipping_year,
            "commodity": commodity,
        }

        return _create_application(
            application_type,
            process_type,
            reference,
            import_fixture_data,
            submit,
            override_status,
            extra_kwargs=wood_kwargs,
        )

    @staticmethod
    def cfs_application(export_fixture_data: ExportFixtureData, country_of_manufacture="Peru"):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.FREE_SALE
        )
        process_type = ProcessTypes.CFS

        com = Country.objects.get(name=country_of_manufacture)
        app: CertificateOfFreeSaleApplication = _create_export_application(
            application_type, process_type, export_fixture_data, False, extra_kwargs={}
        )

        CFSSchedule.objects.create(
            application=app, country_of_manufacture=com, created_by=export_fixture_data.request.user
        )

        _submit_application(app, export_fixture_data)

        return app

    @staticmethod
    def com_application(export_fixture_data: ExportFixtureData, submit=True):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        )
        process_type = ProcessTypes.COM

        return _create_export_application(
            application_type, process_type, export_fixture_data, submit, extra_kwargs={}
        )

    @staticmethod
    def gmp_application(export_fixture_data: ExportFixtureData, submit=True):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.GMP
        )
        process_type = ProcessTypes.GMP

        return _create_export_application(
            application_type, process_type, export_fixture_data, submit, extra_kwargs={}
        )


def _create_application(
    application_type: ImportApplicationType,
    process_type: ProcessTypes,
    reference: str,
    import_fixture_data: FixtureData,
    submit: bool,
    override_status: ImpExpStatus = None,
    extra_kwargs: dict[str, Any] = None,
):
    kwargs = {
        "applicant_reference": reference,
        "importer": import_fixture_data.importer,
        "created_by": import_fixture_data.importer_user,
        "last_updated_by": import_fixture_data.importer_user,
        "application_type": application_type,
        "process_type": process_type,
        "contact": import_fixture_data.importer_user,
    }

    if extra_kwargs:
        kwargs.update(**extra_kwargs)

    models = {
        ProcessTypes.DEROGATIONS: DerogationsApplication,
        ProcessTypes.FA_DFL: DFLApplication,
        ProcessTypes.FA_OIL: OpenIndividualLicenceApplication,
        ProcessTypes.FA_SIL: SILApplication,
        ProcessTypes.IRON_STEEL: IronSteelApplication,
        ProcessTypes.OPT: OutwardProcessingTradeApplication,
        ProcessTypes.SANCTIONS: SanctionsAndAdhocApplication,
        ProcessTypes.SPS: PriorSurveillanceApplication,
        ProcessTypes.TEXTILES: TextilesApplication,
        ProcessTypes.WOOD: WoodQuotaApplication,
    }

    model_cls = models[process_type]

    application = model_cls.objects.create(**kwargs)
    Task.objects.create(
        process=application,
        task_type=Task.TaskType.PREPARE,
        owner=import_fixture_data.importer_user,
    )
    application.licences.create(status=DocumentPackBase.Status.DRAFT)

    if submit:
        _submit_application(application, import_fixture_data)

    if override_status:
        application.status = override_status
        application.save()

    return application


def _create_export_application(
    application_type: ExportApplicationType,
    process_type: ProcessTypes,
    fixture_data: ExportFixtureData,
    submit: bool,
    extra_kwargs: dict | None = None,
    certificate_countries=("Aruba", "Maldives", "Zambia"),
):
    kwargs = {
        # "applicant_reference": reference,
        "exporter": fixture_data.exporter,
        "created_by": fixture_data.exporter_user,
        "last_updated_by": fixture_data.exporter_user,
        "submitted_by": fixture_data.exporter_user,
        "application_type": application_type,
        "process_type": process_type.value,
        "contact": fixture_data.exporter_user,
    }

    if extra_kwargs:
        kwargs.update(**extra_kwargs)

    models = {
        ProcessTypes.COM: CertificateOfManufactureApplication,
        ProcessTypes.GMP: CertificateOfGoodManufacturingPracticeApplication,
        ProcessTypes.CFS: CertificateOfFreeSaleApplication,
    }

    model_cls = models[process_type]

    application = model_cls.objects.create(**kwargs)
    Task.objects.create(
        process=application, task_type=Task.TaskType.PREPARE, owner=fixture_data.exporter_user
    )
    application.certificates.create(status=DocumentPackBase.Status.DRAFT)

    for c in certificate_countries:
        country = Country.objects.get(name=c)
        application.countries.add(country)

    application.save()

    if submit:
        _submit_application(application, fixture_data)

    return application


def _submit_application(application, import_fixture_data: FixtureData | ExportFixtureData):
    """Helper function to submit an application (Using the application code to do so)"""
    case_progress.application_in_progress(application)
    task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

    submit_application(application, import_fixture_data.request, task)
    application.save()


def create_test_commodity(commodity_code):
    com_type = CommodityType.objects.get(type_code="TEXTILES")
    commodity, created = Commodity.objects.get_or_create(
        defaults={"commodity_type": com_type, "validity_start_date": datetime.date.today()},
        commodity_code=commodity_code,
    )
    return commodity


def create_test_commodity_group(category_commodity_group: str, commodity: Commodity):
    group, created = CommodityGroup.objects.get_or_create(group_code=category_commodity_group)

    if created:
        group.commodities.add(commodity)

    return group
