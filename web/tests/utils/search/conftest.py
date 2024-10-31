import datetime as dt
from typing import Any, NamedTuple

import pytest

from web.domains.case._import.legacy.models.opt_models import CP_CATEGORIES
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
    DFLApplication,
    ExportApplicationType,
    Exporter,
    ImportApplicationType,
    Importer,
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
    agent_importer: Importer | None
    importer_user: User
    agent_user: User | None
    ilb_admin_user: User
    request: AuthenticatedHttpRequest


@pytest.fixture
def importer_one_fixture_data(
    db,
    importer,
    ilb_admin_user,
    agent_importer,
    importer_one_contact,
    importer_one_agent_one_contact,
    request,
) -> FixtureData:
    # This is the user who submits the applications in _submit_application
    request.user = importer_one_contact
    request.icms = ICMSMiddlewareContext()

    return FixtureData(
        importer=importer,
        agent_importer=agent_importer,
        importer_user=importer_one_contact,
        agent_user=importer_one_agent_one_contact,
        ilb_admin_user=ilb_admin_user,
        request=request,
    )


@pytest.fixture
def importer_two_fixture_data(
    db, importer_two, ilb_admin_user, importer_two_contact, request
) -> FixtureData:
    # This is the user who submits the applications in _submit_application
    request.user = importer_two_contact
    request.icms = ICMSMiddlewareContext()

    return FixtureData(
        importer=importer_two,
        agent_importer=None,
        importer_user=importer_two_contact,
        agent_user=None,
        ilb_admin_user=ilb_admin_user,
        request=request,
    )


class ExportFixtureData(NamedTuple):
    exporter: Exporter
    agent_exporter: Exporter | None
    exporter_user: User
    exporter_agent_user: User | None
    ilb_admin_user: User
    request: AuthenticatedHttpRequest


@pytest.fixture
def exporter_one_fixture_data(
    db,
    exporter,
    ilb_admin_user,
    agent_exporter,
    exporter_one_contact,
    exporter_one_agent_one_contact,
    request,
):
    # This is the user who submits the applications in _submit_application
    request.user = exporter_one_contact
    request.icms = ICMSMiddlewareContext()

    return ExportFixtureData(
        exporter=exporter,
        agent_exporter=agent_exporter,
        exporter_user=exporter_one_contact,
        exporter_agent_user=exporter_one_agent_one_contact,
        ilb_admin_user=ilb_admin_user,
        request=request,
    )


@pytest.fixture
def exporter_two_fixture_data(
    db,
    exporter_two,
    ilb_admin_user,
    exporter_two_contact,
    request,
):
    # This is the user who submits the applications in _submit_application
    request.user = exporter_two_contact
    request.icms = ICMSMiddlewareContext()

    return ExportFixtureData(
        exporter=exporter_two,
        agent_exporter=None,
        exporter_user=exporter_two_contact,
        exporter_agent_user=None,
        ilb_admin_user=ilb_admin_user,
        request=request,
    )


class Build:
    @staticmethod
    def fa_dfl_application(
        reference,
        importer_conf: FixtureData,
        submit=True,
        origin_country="the Czech Republic",
        consignment_country="the Slovak Republic",
        commodity_code=FirearmCommodity.EX_CHAPTER_97,
        agent_application: bool = False,
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
            importer_conf,
            submit,
            agent_application=agent_application,
            extra_kwargs=fa_dfl_kwargs,
        )

    @staticmethod
    def fa_oil_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit,
            extra_kwargs=fa_oil_kwargs,
        )

    @staticmethod
    def fa_sil_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit,
            extra_kwargs=fa_sil_kwargs,
        )

    @staticmethod
    def opt_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit=False,
            extra_kwargs=opt_kwargs,
        )

        for com in cp_commodities:
            application.cp_commodities.add(com)

        for com in teg_commodities:
            application.teg_commodities.add(com)

        _submit_application(application, importer_conf)

        return application

    @staticmethod
    def sanctionadhoc_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
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
                goods_description_original=f"Some goods: {com}",
                quantity_amount_original=123,
                value_original=123,
            )

        _submit_application(application, importer_conf)

        return application

    @staticmethod
    def sps_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit,
            extra_kwargs=sps_kwargs,
        )

    @staticmethod
    def textiles_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit,
            extra_kwargs=textiles_kwargs,
        )

    @staticmethod
    def wood_application(
        reference,
        importer_conf: FixtureData,
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
            importer_conf,
            submit,
            override_status=override_status,
            extra_kwargs=wood_kwargs,
        )

    @staticmethod
    def cfs_application(exporter_conf: ExportFixtureData, country_of_manufacture="Peru"):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.FREE_SALE
        )
        process_type = ProcessTypes.CFS

        com = Country.objects.get(name=country_of_manufacture)
        app: CertificateOfFreeSaleApplication = _create_export_application(
            application_type, process_type, exporter_conf, False, extra_kwargs={}
        )

        CFSSchedule.objects.create(
            application=app, country_of_manufacture=com, created_by=exporter_conf.request.user
        )

        _submit_application(app, exporter_conf)

        return app

    @staticmethod
    def com_application(exporter_conf: ExportFixtureData, submit=True, agent_application=False):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        )
        process_type = ProcessTypes.COM

        return _create_export_application(
            application_type,
            process_type,
            exporter_conf,
            submit,
            agent_application=agent_application,
            extra_kwargs={},
        )

    @staticmethod
    def gmp_application(exporter_conf: ExportFixtureData, submit=True):
        application_type = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.GMP
        )
        process_type = ProcessTypes.GMP

        return _create_export_application(
            application_type, process_type, exporter_conf, submit, extra_kwargs={}
        )


def _create_application(
    application_type: ImportApplicationType,
    process_type: ProcessTypes,
    reference: str,
    importer_conf: FixtureData,
    submit: bool,
    *,
    override_status: ImpExpStatus = None,
    agent_application: bool = False,
    extra_kwargs: dict[str, Any] = None,
):
    kwargs = {
        "applicant_reference": reference,
        "importer": importer_conf.importer,
        "importer_office": importer_conf.importer.offices.first(),
        "created_by": importer_conf.importer_user,
        "last_updated_by": importer_conf.importer_user,
        "application_type": application_type,
        "process_type": process_type,
        "contact": importer_conf.importer_user,
    }

    if extra_kwargs:
        kwargs.update(**extra_kwargs)

    models = {
        ProcessTypes.FA_DFL: DFLApplication,
        ProcessTypes.FA_OIL: OpenIndividualLicenceApplication,
        ProcessTypes.FA_SIL: SILApplication,
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
        owner=importer_conf.importer_user,
    )
    application.licences.create(status=DocumentPackBase.Status.DRAFT)

    if submit:
        _submit_application(application, importer_conf)

    if override_status:
        application.status = override_status
        application.save()

    if agent_application:
        application.agent = importer_conf.agent_importer
        application.agent_office = importer_conf.agent_importer.offices.first()
        application.save()

    return application


def _create_export_application(
    application_type: ExportApplicationType,
    process_type: ProcessTypes,
    fixture_data: ExportFixtureData,
    submit: bool,
    *,
    agent_application: bool = False,
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

    if agent_application:
        application.agent = fixture_data.agent_exporter
        application.agent_office = fixture_data.agent_exporter.offices.first()
        application.save()

    return application


def _submit_application(application, importer_exporter_conf: FixtureData | ExportFixtureData):
    """Helper function to submit an application (Using the application code to do so)"""
    case_progress.application_in_progress(application)
    task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

    submit_application(application, importer_exporter_conf.request, task)
    application.save()


def create_test_commodity(commodity_code):
    com_type = CommodityType.objects.get(type_code="TEXTILES")
    commodity, created = Commodity.objects.get_or_create(
        defaults={"commodity_type": com_type, "validity_start_date": dt.date.today()},
        commodity_code=commodity_code,
    )
    return commodity


def create_test_commodity_group(category_commodity_group: str, commodity: Commodity):
    group, created = CommodityGroup.objects.get_or_create(group_code=category_commodity_group)

    if created:
        group.commodities.add(commodity)

    return group
