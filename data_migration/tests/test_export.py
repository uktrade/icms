from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration import models
from data_migration.queries import DATA_TYPE_QUERY_MODEL, DATA_TYPE_XML

from . import factory, xml_data


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
        call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert not models.User.objects.exists()
    assert not models.Office.objects.exists()
    assert not models.Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_no_pw(mock_connect):
    with pytest.raises(CommandError, match="No user details found for this environment"):
        call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert not models.User.objects.exists()
    assert not models.Office.objects.exists()
    assert not models.Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user(mock_connect):
    call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert models.User.objects.exists()
    assert models.Office.objects.exists()
    assert models.Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_exists(mock_connect):
    models.User.objects.create(username="Username")
    call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert models.User.objects.count() == 1


class MockCursor:
    def __init__(self, *args, **kwargs):
        self.fetched = False
        self.rows = None
        self.description = [("country_group_id",), ("name",), ("comments",)]

    @staticmethod
    def execute(query):
        return

    @staticmethod
    def close():
        return

    def fetchmany(self, *args):
        if not self.fetched:
            self.rows = self.fetch_rows()
            self.fetched = True

        return next(self.rows)

    @staticmethod
    def fetch_rows():
        yield [
            ("A", "TEST GROUP A", None),
            ("B", "TEST GROUP B", "Comment B"),
            ("C", "TEST GROUP C", "Comment C"),
        ]
        yield None


class MockConnect:
    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, type, value, traceback):
        pass

    @staticmethod
    def cursor():
        return MockCursor()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, {"reference": [("REF", models.CountryGroup)]})
@mock.patch.object(cx_Oracle, "connect")
def test_export_data(mock_connect):
    mock_connect.return_value = MockConnect()
    call_command("export_from_v1", "--skip_user", "--skip_ia")
    assert models.CountryGroup.objects.filter(country_group_id__in=["A", "B", "C"]).count() == 3


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, {"import_application": []})
@mock.patch.dict(
    DATA_TYPE_XML,
    {
        "import_application": [
            (
                models.OpenIndividualLicenceApplication,
                "bought_from_details_xml",
                models.ImportContact,
            ),
            (
                models.OILSupplementaryInfo,
                "supplementary_report_xml",
                models.OILSupplementaryReport,
            ),
            (
                models.OILSupplementaryReport,
                "report_firearms_xml",
                models.OILSupplementaryReportFirearm,
            ),
        ]
    },
)
@mock.patch.object(cx_Oracle, "connect")
def test_extract_xml(mock_connect):

    mock_connect.return_value = MockConnect()
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

        models.ImportApplicationLicence.objects.create(imad=ia, status="AC")
        factory.OILApplicationFactory(pk=pk, imad=ia)

        factory.OILSupplementaryInfoFactory(imad=ia, supplementary_report_xml=supp_xmls[i])

    call_command("export_from_v1", "--skip_user", "--skip_ref")

    reports = models.OILSupplementaryReport.objects.filter(supplementary_info__imad_id__in=pk_range)
    assert reports.count() == 4
    assert reports.filter(transport="AIR").count() == 1
    assert reports.filter(transport="RAIL").count() == 1
    assert reports.filter(transport__isnull=True).count() == 2

    firearms = models.OILSupplementaryReportFirearm.objects.filter(report__in=reports)
    assert firearms.count() == 5
    assert firearms.filter(is_upload=True, is_manual=False, is_no_firearm=False).count() == 1
    assert firearms.filter(is_upload=False, is_manual=True, is_no_firearm=False).count() == 4
