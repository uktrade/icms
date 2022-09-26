from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command
from django.test import override_settings

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

from . import factory, utils

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
        (dm.CommodityType, web.CommodityType),
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
        (q_ref, "commodity_type", dm.CommodityType),
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


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, opt_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, opt_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, opt_query_model)
@mock.patch.dict(DATA_TYPE_XML, opt_xml)
def test_import_export_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("extract_v1_xml")
    call_command("import_v1_data")

    assert web.OutwardProcessingTradeApplication.objects.count() == 2
    opt1, opt2 = web.OutwardProcessingTradeApplication.objects.order_by("pk")
    assert opt1.cp_commodities.count() == 3
    assert opt1.teg_commodities.count() == 3
    assert opt2.cp_commodities.count() == 0
    assert opt2.teg_commodities.count() == 0


sps_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
        (dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sps_data_source_target)
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
    {"file": [(q_f, "sps_application_files", dm.FileCombined)]},
)
def test_import_sps_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    dm.User.objects.create(id=2, username="test_user")
    dm.Importer.objects.create(id=2, name="test_org", type="ORGANISATION")

    call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_user", "--skip_export")

    factory.CountryFactory(id=1, name="My Test Country")
    cg = dm.CountryGroup.objects.create(country_group_id="SPS", name="SPS")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 2))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=i + 1000,
            application_type=iat,
            created_by_id=2,
            last_updated_by_id=2,
            importer_id=2,
            file_folder_id=i + 100,
        )

        dm.ImportApplicationLicence.objects.create(ima=process, status="AC", imad_id=ia.imad_id)

        dm.PriorSurveillanceContractFile.objects.create(
            imad=ia,
            file_type="PRO_FORMA_INVOICE" if i == 0 else "SUPPLY_CONTRACT",
            target_id=i + 1000,
        )
        sps_data = {
            "pk": pk,
            "imad": ia,
            "quantity": "NONSENSE" if i == 0 else 100,
            "value_gbp": "NONSENSE" if i == 0 else 100,
            "value_eur": "NONSENSE" if i == 0 else 100,
        }
        dm.PriorSurveillanceApplication.objects.create(**sps_data)

    call_command("import_v1_data", "--skip_export")

    assert web.PriorSurveillanceApplication.objects.count() == 2
    assert web.PriorSurveillanceContractFile.objects.count() == 2

    sps1, sps2 = web.PriorSurveillanceApplication.objects.order_by("pk").all()

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
