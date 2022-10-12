from datetime import datetime
from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command

from data_migration import models as dm
from data_migration.queries import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
from data_migration.queries import files as q_f
from data_migration.queries import import_application as q_ia
from data_migration.queries import reference as q_ref
from data_migration.queries import user as q_u
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
    "user": [],
    "file": [
        (q_f, "opt_application_files", dm.FileCombined),
    ],
    "import_application": [
        (q_u, "importers", dm.Importer),
        (q_u, "importer_offices", dm.Office),
        (q_ia, "ia_type", dm.ImportApplicationType),
        (q_ia, "opt_application", dm.OutwardProcessingTradeApplication),
    ],
    "export_application": [],
    "reference": [
        (q_ref, "country_group", dm.CountryGroup),
        (q_ref, "country", dm.Country),
        (q_ref, "unit", dm.Unit),
        (q_ref, "commodity_type", dm.CommodityType),
        (q_ref, "commodity_group", dm.CommodityGroup),
        (q_ref, "commodity", dm.Commodity),
    ],
}

opt_m2m = {
    "export_application": [],
    "import_application": [
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
}

opt_xml = {
    "export_application": [],
    "import_application": [
        xml_parser.OPTCpCommodity,
        xml_parser.OPTTegCommodity,
    ],
}


@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
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
    assert opt1.last_export_day == datetime(2023, 4, 23).date()
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
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
        (dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
        (dm.SanctionsAndAdhocApplication, web.SanctionsAndAdhocApplication),
        (dm.SanctionsAndAdhocApplicationGoods, web.SanctionsAndAdhocApplicationGoods),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sps_data_source_target)
@mock.patch.dict(
    DATA_TYPE_XML,
    {
        "export_application": [],
        "import_application": [xml_parser.SanctionGoodsParser],
    },
)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [
            (dm.SPSSupportingDoc, web.PriorSurveillanceApplication, "supporting_documents")
        ]
    },
)
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "file": [
            (q_f, "sps_application_files", dm.FileCombined),
            (q_f, "sps_docs", dm.FileCombined),
            (q_f, "sanction_application_files", dm.FileCombined),
        ],
        "import_application": [
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
            (q_ia, "ia_type", dm.ImportApplicationType),
            (q_ia, "sps_application", dm.PriorSurveillanceApplication),
            (q_ia, "sanctions_application", dm.SanctionsAndAdhocApplication),
        ],
        "reference": [
            (q_ref, "country_group", dm.CountryGroup),
            (q_ref, "country", dm.Country),
            (q_ref, "commodity_type", dm.CommodityType),
            (q_ref, "commodity", dm.Commodity),
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
    assert sps1.supporting_documents.count() == 2
    assert sps1.quantity is None
    assert sps1.value_gbp is None
    assert sps1.value_eur is None

    assert sps2.contract_file.file_type == "supply_contract"
    assert sps2.supporting_documents.count() == 1
    assert sps2.quantity == 100
    assert sps2.value_gbp == 100
    assert sps2.value_eur == 100

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
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.CommodityType, web.CommodityType),
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
        "file": [
            (q_f, "textiles_application_files", dm.FileCombined),
        ],
        "import_application": [
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
            (q_ia, "ia_type", dm.ImportApplicationType),
            (q_ia, "textiles_application", dm.TextilesApplication),
            (q_ia, "textiles_checklist", dm.TextilesChecklist),
        ],
        "export_application": [],
        "reference": [
            (q_ref, "country_group", dm.CountryGroup),
            (q_ref, "country", dm.Country),
            (q_ref, "commodity_type", dm.CommodityType),
            (q_ref, "commodity", dm.Commodity),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, tex_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, {"import_application": []})
@mock.patch.object(cx_Oracle, "connect")
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
