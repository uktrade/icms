import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command

from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
from data_migration.management.commands.types import QueryModel
from data_migration.utils import xml_parser
from web import models as web

from . import utils

opt_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Office, web.Office),
        (dm.Process, web.Process),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.Unit, web.Unit),
        (dm.CommodityType, web.CommodityType),
        (dm.CommodityGroup, web.CommodityGroup),
        (dm.Commodity, web.Commodity),
        (dm.Template, web.Template),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.ImportApplication, web.ImportApplication),
        (dm.OutwardProcessingTradeApplication, web.OutwardProcessingTradeApplication),
    ],
    "export_application": [],
    "file": [
        (dm.File, web.File),
    ],
}

opt_query_model = {
    "user": [
        QueryModel(queries.users, "users", dm.User),
        QueryModel(queries.importers, "importers", dm.Importer),
        QueryModel(queries.importer_offices, "importer_offices", dm.Office),
    ],
    "file_folder": [
        QueryModel(
            queries.import_application_folders, "Import Application File Folders", dm.FileFolder
        ),
        QueryModel(
            queries.import_application_file_targets,
            "Import Application File Targets",
            dm.FileTarget,
        ),
    ],
    "file": [
        QueryModel(queries.import_application_files, "Import Application Files", dm.File),
    ],
    "import_application": [
        QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
        QueryModel(
            queries.opt_application, "opt_application", dm.OutwardProcessingTradeApplication
        ),
    ],
    "export_application": [],
    "reference": [
        QueryModel(queries.country_group, "country_group", dm.CountryGroup),
        QueryModel(queries.country, "country", dm.Country),
        QueryModel(queries.unit, "unit", dm.Unit),
        QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
        QueryModel(queries.commodity_group, "commodity_group", dm.CommodityGroup),
        QueryModel(queries.commodity, "commodity", dm.Commodity),
        QueryModel(queries.template, "templates", dm.Template),
    ],
}

opt_m2m = {
    "export_application": [],
    "import_application": [],
    "file": [
        (
            dm.OPTCpCommodity,
            web.OutwardProcessingTradeApplication,
            "cp_commodities",
        ),
        (
            dm.OPTTegCommodity,
            web.OutwardProcessingTradeApplication,
            "teg_commodities",
        ),
    ],
    "user": [],
}

opt_xml = {
    "export_application": [],
    "import_application": [
        xml_parser.OPTCpCommodity,
        xml_parser.OPTTegCommodity,
    ],
    "user": [],
}


@pytest.mark.django_db
@mock.patch.object(oracledb, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, opt_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, opt_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, opt_query_model)
@mock.patch.dict(DATA_TYPE_XML, opt_xml)
def test_import_export_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("extract_v1_xml")
    call_command("import_v1_data")

    assert web.OutwardProcessingTradeApplication.objects.count() == 2
    opt1, opt2 = web.OutwardProcessingTradeApplication.objects.order_by("pk")

    assert opt1.customs_office_name == "Test"
    assert opt1.customs_office_address == "Test Address"
    assert opt1.rate_of_yield == 0.5
    assert opt1.rate_of_yield_calc_method == "abc"
    assert opt1.last_export_day == dt.date(2023, 4, 23)
    assert opt1.reimport_period == 12

    assert opt1.nature_process_ops == "test"
    assert opt1.suggested_id == "test"
    assert opt1.cp_origin_country_id == 1
    assert opt1.cp_processing_country_id == 1
    assert opt1.commodity_group_id == 1
    assert opt1.cp_total_quantity == 123
    assert opt1.cp_total_value == 100
    assert opt1.teg_origin_country_id == 1
    assert opt1.fq_similar_to_own_factory == "Y"
    assert opt1.fq_manufacturing_within_eu == "Y"
    assert opt1.fq_maintained_in_eu == "Y"
    assert opt1.fq_maintained_in_eu_reasons == "test eu"
    assert opt1.fq_employment_decreased == "N"
    assert opt1.fq_employment_decreased_reasons == "test em"
    assert opt1.fq_prior_authorisation == "Y"
    assert opt1.fq_prior_authorisation_reasons == "test pa"
    assert opt1.fq_past_beneficiary == "Y"
    assert opt1.fq_past_beneficiary_reasons == "test pb"
    assert opt1.fq_new_application == "Y"
    assert opt1.fq_new_application_reasons == "test na"
    assert opt1.fq_further_authorisation == "Y"
    assert opt1.fq_further_authorisation_reasons == "test fa"
    assert opt1.fq_subcontract_production == "Y"
    assert opt1.cp_commodities.count() == 3
    assert opt1.teg_commodities.count() == 3
    assert opt2.cp_commodities.count() == 0
    assert opt2.teg_commodities.count() == 0


sps_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Office, web.Office),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.CommodityType, web.CommodityType),
        (dm.Commodity, web.Commodity),
        (dm.Template, web.Template),
        (dm.UniqueReference, web.UniqueReference),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
        (dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
        (dm.SanctionsAndAdhocApplication, web.SanctionsAndAdhocApplication),
        (dm.SanctionsAndAdhocApplicationGoods, web.SanctionsAndAdhocApplicationGoods),
        (dm.SIGLTransmission, web.SIGLTransmission),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@pytest.mark.django_db
@mock.patch.object(oracledb, "connect")
@mock.patch.dict(DATA_TYPE_XML, {"import_application": [], "user": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sps_data_source_target)
@mock.patch.dict(
    DATA_TYPE_XML,
    {
        "export_application": [],
        "import_application": [xml_parser.SanctionGoodsParser],
        "user": [],
    },
)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [
            (dm.SIGLTransmission, web.ImportApplication, "sigl_transmissions"),
        ],
        "user": [],
        "file": [
            (dm.SPSSupportingDoc, web.PriorSurveillanceApplication, "supporting_documents"),
        ],
    },
)
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "file_folder": [
            QueryModel(
                queries.import_application_folders, "Import Application File Folders", dm.FileFolder
            ),
            QueryModel(
                queries.import_application_file_targets,
                "Import Application File Targets",
                dm.FileTarget,
            ),
        ],
        "file": [
            QueryModel(queries.import_application_files, "Import Application Files", dm.File),
        ],
        "import_application": [
            QueryModel(
                queries.ia_licence_doc_refs, "Import Licence Doc References", dm.UniqueReference
            ),
            QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
            QueryModel(queries.sps_application, "sps_application", dm.PriorSurveillanceApplication),
            QueryModel(
                queries.sanctions_application,
                "sanctions_application",
                dm.SanctionsAndAdhocApplication,
            ),
            QueryModel(queries.sigl_transmission, "sigl_transmission", dm.SIGLTransmission),
        ],
        "reference": [
            QueryModel(queries.country_group, "country_group", dm.CountryGroup),
            QueryModel(queries.country, "country", dm.Country),
            QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
            QueryModel(queries.commodity, "commodity", dm.Commodity),
            QueryModel(queries.template, "templates", dm.Template),
        ],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.importers, "importers", dm.Importer),
            QueryModel(queries.importer_offices, "importer_offices", dm.Office),
        ],
    },
)
def test_import_sps_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_export")
    call_command("extract_v1_xml")
    call_command("import_v1_data", "--skip_export")

    assert web.PriorSurveillanceApplication.objects.count() == 2
    assert web.PriorSurveillanceContractFile.objects.count() == 2

    sps1, sps2 = web.PriorSurveillanceApplication.objects.order_by("pk")

    assert sps1.contract_file.file_type == "pro_forma_invoice"
    assert sps1.contract_file.filename == "contract-no-content.pdf"
    assert sps1.supporting_documents.count() == 2
    assert set(sps1.supporting_documents.values_list("path", flat=True)) == {
        "contract/file/10002",
        "contract/file/10003",
    }
    assert sps1.endorsements.count() == 0
    assert sps1.status == "COMPLETED"
    assert sps1.reference == "IMA/2022/10234"
    assert sps1.decision == "APPROVE"
    assert sps1.legacy_case_flag is False
    assert sps1.licence_extended_flag is False
    assert sps1.submitted_by.full_name == "Mr ILB Case-Officer"
    assert sps1.created_by.full_name == "Mr ILB Case-Officer"
    assert sps1.last_updated_by.full_name == "Mr ILB Case-Officer"
    assert sps1.importer.name == "Test Org"
    assert sps1.importer_office.postcode == "ABC"
    assert sps1.contact.full_name == "Mr ILB Case-Officer"
    assert sps1.is_active is True
    assert sps1.commodity.commodity_code == "1000"
    assert sps1.customs_cleared_to_uk is True
    assert sps1.chief_usage_status == "D"

    assert sps1.create_datetime == dt.datetime(2022, 4, 22, 0, 0, 0, tzinfo=dt.UTC)
    assert sps1.created == dt.datetime(2022, 4, 22, 0, 0, 0, tzinfo=dt.UTC)
    assert sps1.submit_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps1.last_submit_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps1.last_update_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps1.order_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)

    none_fields = [
        "finished",
        "reassign_datetime",
        "refuse_reason",
        "applicant_reference",
        "variation_decision",
        "variation_refuse_reason",
        "agent_id",
        "agent_office_id",
        "origin_country_id",
        "consignment_country_id",
        "commodity_group_id",
        "case_owner_id",
        "cover_letter_text",
        "imi_submitted_by_id",
        "imi_submit_datetime",
    ]

    for field in none_fields + ["quantity", "value_gbp", "value_eur"]:
        assert getattr(sps1, field) is None

    assert sps1.contract_file.filename == "contract-no-content.pdf"
    assert sps1.contract_file.content_type == "application/pdf"

    ia1 = sps1.importapplication_ptr
    assert ia1.sigl_transmissions.count() == 3

    st1, st2, st3 = ia1.sigl_transmissions.order_by("pk")
    assert st1.status == "ACCEPTED"
    assert st1.transmission_type == "WEB_SERVICE"
    assert st1.request_type == "INSERT"
    assert st1.response_message == "Successful processing"
    assert st1.response_code == 0
    assert st2.request_type == "CONFIRM"
    assert st3.request_type == "DELETE"

    for field in none_fields:
        assert getattr(sps2, field) is None

    assert sps2.quantity == 100
    assert sps2.value_gbp == 100
    assert sps2.value_eur == 100
    assert sps2.status == "COMPLETED"
    assert sps2.reference == "IMA/2022/10235"
    assert sps2.decision == "APPROVE"
    assert sps2.legacy_case_flag is False
    assert sps2.licence_extended_flag is False
    assert sps2.submitted_by.full_name == "Mr ILB Case-Officer"
    assert sps2.created_by.full_name == "Mr ILB Case-Officer"
    assert sps2.last_updated_by.full_name == "Mr ILB Case-Officer"
    assert sps2.importer.name == "Test Org"
    assert sps2.importer_office.postcode == "ABC"
    assert sps2.contact.full_name == "Mr ILB Case-Officer"
    assert sps2.is_active is True
    assert sps2.commodity.commodity_code == "1001"
    assert sps2.customs_cleared_to_uk is False
    assert sps2.chief_usage_status == "E"

    assert sps2.create_datetime == dt.datetime(2022, 4, 22, 0, 0, 0, tzinfo=dt.UTC)
    assert sps2.created == dt.datetime(2022, 4, 22, 0, 0, 0, tzinfo=dt.UTC)
    assert sps2.submit_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps2.last_submit_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps2.last_update_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)
    assert sps2.order_datetime == dt.datetime(2022, 4, 23, 0, 0, 0, tzinfo=dt.UTC)

    assert sps2.contract_file.file_type == "supply_contract"
    assert sps2.supporting_documents.count() == 1
    assert set(sps2.supporting_documents.values_list("path", flat=True)) == {"contract/file/10004"}
    assert sps2.endorsements.count() == 0

    assert sps2.contract_file.filename == "contract-2.pdf"
    assert sps2.contract_file.content_type == "pdf"

    ia2 = sps2.importapplication_ptr
    assert ia2.sigl_transmissions.count() == 2

    st4, st5 = ia2.sigl_transmissions.order_by("pk")
    assert st4.status == "REJECTED"
    assert st4.transmission_type == "MANUAL"
    assert st4.request_type == "INSERT"
    assert st4.response_message == "Something missing"
    assert st4.response_code == 500

    assert st5.status == "ACCEPTED"
    assert st5.transmission_type == "MANUAL"
    assert st5.request_type == "INSERT"
    assert st5.response_message is None
    assert st5.response_code is None

    assert web.SanctionsAndAdhocApplication.objects.count() == 1
    san = web.SanctionsAndAdhocApplication.objects.first()
    assert san.exporter_name == "Test Exporter"
    assert san.exporter_address == "123 Somewhere"
    assert web.SanctionsAndAdhocApplicationGoods.objects.count() == 2
    sg1, sg2 = web.SanctionsAndAdhocApplicationGoods.objects.order_by("pk")
    assert sg1.goods_description == "Nice things"
    assert sg1.import_application_id == san.id
    assert sg1.quantity_amount == 3.00
    assert sg1.value == 75
    assert sg1.commodity_id == 1

    assert sg2.goods_description == "More nice things"
    assert sg2.import_application_id == san.id
    assert sg2.quantity_amount == 1.00
    assert sg2.value == 100
    assert sg2.commodity_id == 2


tex_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Office, web.Office),
    ],
    "reference": [
        (dm.Unit, web.Unit),
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.CommodityType, web.CommodityType),
        (dm.CommodityGroup, web.CommodityGroup),
        (dm.Commodity, web.Commodity),
        (dm.Template, web.Template),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.TextilesApplication, web.TextilesApplication),
        (dm.TextilesChecklist, web.TextilesChecklist),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "file_folder": [
            QueryModel(
                queries.import_application_folders, "Import Application File Folders", dm.FileFolder
            ),
            QueryModel(
                queries.import_application_file_targets,
                "Import Application File Targets",
                dm.FileTarget,
            ),
        ],
        "file": [
            QueryModel(queries.import_application_files, "Import Application Files", dm.File),
        ],
        "import_application": [
            QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
            QueryModel(
                queries.textiles_application, "textiles_application", dm.TextilesApplication
            ),
            QueryModel(queries.textiles_checklist, "textiles_checklist", dm.TextilesChecklist),
        ],
        "export_application": [],
        "reference": [
            QueryModel(queries.unit, "unit", dm.Unit),
            QueryModel(queries.country_group, "country_group", dm.CountryGroup),
            QueryModel(queries.country, "country", dm.Country),
            QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
            QueryModel(queries.commodity_group, "commodity_group", dm.CommodityGroup),
            QueryModel(queries.commodity, "commodity", dm.Commodity),
            QueryModel(queries.template, "templates", dm.Template),
        ],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.importers, "importers", dm.Importer),
            QueryModel(queries.importer_offices, "importer_offices", dm.Office),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, tex_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, {"import_application": [], "file": []})
@mock.patch.object(oracledb, "connect")
def test_import_textiles_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_export")
    call_command("import_v1_data", "--skip_export")

    tex1, tex2, tex3 = web.TextilesApplication.objects.order_by("pk")
    assert tex1.checklist.case_update == "no"
    assert tex1.checklist.fir_required == "n/a"
    assert tex1.checklist.response_preparation is True
    assert tex1.checklist.authorisation is True

    assert tex2.checklist.case_update == "yes"
    assert tex2.checklist.fir_required == "no"
    assert tex2.checklist.response_preparation is True
    assert tex2.checklist.authorisation is False

    assert hasattr(tex3, "checklist") is False

    assert web.CommodityGroup.objects.count() == 2
    assert web.CommodityGroup.objects.first().start_datetime == dt.datetime(
        2022, 12, 31, 12, 30, tzinfo=dt.UTC
    )
    assert web.Commodity.objects.count() == 5
    assert web.Commodity.objects.first().start_datetime == dt.datetime(
        2022, 12, 31, 12, 30, tzinfo=dt.UTC
    )
