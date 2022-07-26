from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration import models, queries
from data_migration.queries import import_application, reference
from data_migration.utils import xml_parser

from . import factory, utils, xml_data


@override_settings(ALLOW_DATA_MIGRATION=False)
@override_settings(APP_ENV="production")
def test_data_migration_not_enabled():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("export_from_v1")


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="test")
def test_data_migration_not_enabled_non_prod():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("export_from_v1")


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_no_username(mock_connect):
    with pytest.raises(CommandError, match="No user details found for this environment"):
        call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_file")

    assert not models.User.objects.exists()
    assert not models.Office.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_no_pw(mock_connect):
    with pytest.raises(CommandError, match="No user details found for this environment"):
        call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_file")

    assert not models.User.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user(mock_connect):
    call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_file")

    assert models.User.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_exists(mock_connect):
    models.User.objects.create(username="Username")
    call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_file")

    assert models.User.objects.count() == 1


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(
    queries.DATA_TYPE_QUERY_MODEL,
    {"reference": [(reference, "country_group", models.CountryGroup)], "file": []},
)
@mock.patch.object(cx_Oracle, "connect")
def test_export_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1", "--skip_user", "--skip_ia", "--skip_file")
    assert models.CountryGroup.objects.filter(country_group_id__in=["A", "B", "C"]).count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(
    queries.DATA_TYPE_XML,
    {
        "import_application": [
            xml_parser.ImportContactParser,
            xml_parser.OILSupplementaryReportParser,
            xml_parser.OILReportFirearmParser,
        ]
    },
)
@mock.patch.object(cx_Oracle, "connect")
def test_extract_xml(mock_connect):

    mock_connect.return_value = utils.MockConnect()
    user_pk = models.User.objects.count() + 1
    models.User.objects.create(id=user_pk, username="test_import_user")

    importer_pk = models.Importer.objects.count() + 1
    models.Importer.objects.create(id=importer_pk, name="test_import_org", type="ORGANISATION")

    factory.CountryFactory(id=1000, name="My Test Country")

    cg = models.CountryGroup.objects.create(country_group_id="OIL", name="OIL")

    process_pk = models.Process.objects.count() + 1
    pk_range = list(range(process_pk, process_pk + 3))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    supp_xmls = [xml_data.sr_upload_xml, xml_data.sr_manual_xml, xml_data.sr_list]

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type="OIL", ima_id=pk)

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=pk,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
        )

        models.ImportApplicationLicence.objects.create(ima=process, status="AC", legacy_id=i + 1)
        models.OpenIndividualLicenceApplication.objects.create(pk=pk, imad=ia)

        factory.OILSupplementaryInfoFactory(imad=ia, supplementary_report_xml=supp_xmls[i])

    call_command("extract_v1_xml")

    reports = models.OILSupplementaryReport.objects.filter(supplementary_info__imad_id__in=pk_range)
    assert reports.count() == 4
    assert reports.filter(transport="AIR").count() == 1
    assert reports.filter(transport="RAIL").count() == 1
    assert reports.filter(transport__isnull=True).count() == 2

    firearms = models.OILSupplementaryReportFirearm.objects.filter(report__in=reports)
    assert firearms.count() == 5
    assert firearms.filter(is_upload=True, is_manual=False, is_no_firearm=False).count() == 1
    assert firearms.filter(is_upload=False, is_manual=True, is_no_firearm=False).count() == 4


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, {"file": []})
@mock.patch.object(
    queries,
    "FILE_MODELS",
    [
        models.FileFolder,
        models.FileTarget,
        models.File,
    ],
)
@mock.patch.object(cx_Oracle, "connect")
def test_export_files_data(mock_connect):

    mock_connect.return_value = utils.MockConnect()
    user_pk = models.User.objects.count() + 1
    user = models.User.objects.create(id=user_pk, username="test_import_user")
    user_id = user.id

    models.FileCombined.objects.bulk_create(
        [
            models.FileCombined(
                folder_id=f_id,
                folder_type=f_type,
                target_id=t_type and f_id * t_id,
                target_type=t_type,
                status=t_type and "RECEIVED",
                version_id=t_type and v_id * t_id,
                filename=t_type and v,
                content_type=t_type and v,
                file_size=t_type and v_id,
                path=t_type and v,
                created_by_id=user_id,
            )
            for f_id, f_type in enumerate(["F1", "F2"], start=1)
            for t_id, t_type in enumerate(["T1", "T2", None], start=3)
            for v_id, v in enumerate(["a", "b", "c"], start=9)
        ]
    )

    call_command("export_from_v1", "--skip_user", "--skip_ref", "--skip_ia")

    assert models.FileFolder.objects.count() == 2
    assert models.FileTarget.objects.count() == 4
    assert models.File.objects.count() == 12

    assert models.FileFolder.objects.get(folder_id=1).file_targets.count() == 2
    assert models.FileFolder.objects.get(folder_id=2).file_targets.count() == 2

    assert models.FileTarget.objects.get(target_id=3).files.count() == 3
    assert models.FileTarget.objects.get(target_id=4).files.count() == 3
    assert models.FileTarget.objects.get(target_id=6).files.count() == 3
    assert models.FileTarget.objects.get(target_id=8).files.count() == 3


test_query_model = {
    "reference": [
        (reference, "country", models.Country),
        (reference, "country_group", models.CountryGroup),
        (reference, "unit", models.Unit),
    ],
    "file": [],
    "import_application": [
        (reference, "constabularies", models.Constabulary),
        (reference, "obsolete_calibre_group", models.ObsoleteCalibreGroup),
        (import_application, "section5_clauses", models.Section5Clause),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(cx_Oracle, "connect")
def test_export_from_ref_2(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--start=ref.2")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 3
    assert models.Unit.objects.count() == 3
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(cx_Oracle, "connect")
def test_export_from_r_3(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--start=r.3")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 3
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(cx_Oracle, "connect")
def test_export_from_import_application(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--start=import_application.0")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(cx_Oracle, "connect")
def test_export_from_ia(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--start=ia.1")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 3
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="test@example.com")  # /PS-IGNORE
@override_settings(ICMS_PROD_PASSWORD="testpass")
@pytest.mark.django_db
@mock.patch.dict(queries.DATA_TYPE_QUERY_MODEL, test_query_model)
@mock.patch.object(cx_Oracle, "connect")
def test_export_from_ia_2(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--start=ia.2")

    assert models.Country.objects.count() == 0
    assert models.CountryGroup.objects.count() == 0
    assert models.Unit.objects.count() == 0
    assert models.Constabulary.objects.count() == 0
    assert models.ObsoleteCalibreGroup.objects.count() == 3
    assert models.Section5Clause.objects.count() == 3
