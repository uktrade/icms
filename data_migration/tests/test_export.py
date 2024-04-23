import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from data_migration import models, queries
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_XML,
)
from data_migration.management.commands.types import QueryModel
from data_migration.utils import xml_parser

from . import factory, utils
from .utils import xml_data


@override_settings(ALLOW_DATA_MIGRATION=False)
def test_data_migration_not_enabled():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("export_from_v1")


@override_settings(ALLOW_DATA_MIGRATION=True)
@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "reference": [QueryModel(queries.country_group, "country_group", models.CountryGroup)],
        "file": [],
    },
)
@mock.patch.object(oracledb, "connect")
def test_export_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1", "--skip_user", "--skip_ia", "--skip_file", "--skip_export")
    assert models.CountryGroup.objects.filter(country_group_id__in=["A", "B", "C"]).count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_XML,
    {
        "import_application": [
            xml_parser.ImportContactParser,
            xml_parser.OILSupplementaryReportParser,
            xml_parser.OILReportFirearmParser,
        ],
        "user": [],
    },
)
@mock.patch.object(oracledb, "connect")
def test_extract_xml(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    user_pk = models.User.objects.count() + 1
    models.User.objects.create(
        id=user_pk, username="test_import_user", salt="1234", encrypted_password="password"
    )

    importer_pk = models.Importer.objects.count() + 1
    models.Importer.objects.create(id=importer_pk, name="test_import_org", type="ORGANISATION")

    factory.CountryFactory(id=1000, name="My Test Country")

    cg = models.CountryGroup.objects.create(country_group_id="OIL", name="OIL")

    process_pk = models.Process.objects.count() + 1
    pk_range = list(range(process_pk, process_pk + 3))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)
    models.File.objects.create(
        created_by_id=user_pk,
        sr_goods_file_id="abcde",
        filename="SR Upload.pdf",
        content_type="pdf",
        created_datetime=dt.datetime(2022, 11, 5, 12, 11, 3, tzinfo=dt.UTC),
        path="abcde/SR Upload.pdf",
        file_size=1234,
    )

    supp_xmls = [xml_data.sr_upload_xml, xml_data.sr_manual_xml, xml_data.sr_list]

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(
            pk=pk, process_type="OIL", ima_id=pk, created=timezone.now()
        )

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETED",
            imad_id=pk,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
        )

        models.ImportApplicationLicence.objects.create(
            ima=process, status="AC", imad_id=ia.imad_id, created_at=timezone.now()
        )
        models.OpenIndividualLicenceApplication.objects.create(pk=pk, imad=ia)

        factory.OILSupplementaryInfoFactory(imad=ia, supplementary_report_xml=supp_xmls[i])

    call_command("extract_v1_xml", "--skip_export")

    reports = models.OILSupplementaryReport.objects.filter(supplementary_info__imad_id__in=pk_range)
    assert reports.count() == 4
    assert reports.filter(transport="AIR").count() == 1
    assert reports.filter(transport="RAIL").count() == 1
    assert reports.filter(transport__isnull=True).count() == 2

    firearms = models.OILSupplementaryReportFirearm.objects.filter(report__in=reports)
    assert firearms.count() == 5
    assert firearms.filter(is_upload=True, is_manual=False, is_no_firearm=False).count() == 1
    assert firearms.filter(is_upload=False, is_manual=True, is_no_firearm=False).count() == 4


test_query_model = {
    "reference": [
        QueryModel(queries.country, "country", models.Country),
        QueryModel(queries.country_group, "country_group", models.CountryGroup),
        QueryModel(queries.unit, "unit", models.Unit),
    ],
    "file_folder": [],
    "file": [],
    "user": [queries.users, "users", models.User],
    "import_application": [
        QueryModel(queries.constabularies, "constabularies", models.Constabulary),
        QueryModel(
            queries.obsolete_calibre_group, "obsolete_calibre_group", models.ObsoleteCalibreGroup
        ),
        QueryModel(queries.section5_clauses, "section5_clauses", models.Section5Clause),
    ],
}


def create_dummy_user():
    models.User.objects.create(
        id=2,
        username="user",
        first_name="Prod",
        last_name="User",
        is_active=True,
        title="Mr",
        password_disposition="FULL",
        salt="1234",
        encrypted_password="abcd",
    )


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(oracledb, "connect")
def test_export_from_ref_2(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    create_dummy_user()

    call_command("export_from_v1", "--start=ref.2", "--skip_export")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 3
    assert models.Unit.objects.count() == 3
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(oracledb, "connect")
def test_export_from_r_3(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    create_dummy_user()

    call_command("export_from_v1", "--start=r.3", "--skip_export")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 3
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(oracledb, "connect")
def test_export_from_import_application(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    create_dummy_user()

    call_command("export_from_v1", "--start=import_application.0", "--skip_export")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(oracledb, "connect")
def test_export_from_ia(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    create_dummy_user()

    call_command("export_from_v1", "--start=ia.1", "--skip_export")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(oracledb, "connect")
def test_export_from_ia_2(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    create_dummy_user()

    call_command("export_from_v1", "--start=ia.2", "--skip_export")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 0
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3
