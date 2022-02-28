from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration.models import CountryGroup, Importer, Office, User
from data_migration.queries import DATA_TYPE_QUERY_MODEL


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

    assert not User.objects.exists()
    assert not Office.objects.exists()
    assert not Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_no_pw(mock_connect):
    with pytest.raises(CommandError, match="No user details found for this environment"):
        call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert not User.objects.exists()
    assert not Office.objects.exists()
    assert not Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user(mock_connect):
    call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert User.objects.exists()
    assert Office.objects.exists()
    assert Importer.objects.exists()


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
def test_create_user_exists(mock_connect):
    User.objects.create(username="Username")
    call_command("export_from_v1", "--skip_ref", "--skip_ia")

    assert User.objects.count() == 1


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
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, {"reference": [("REF", CountryGroup)]})
@mock.patch.object(cx_Oracle, "connect")
def test_export_data(mock_connect):
    mock_connect.return_value = MockConnect()
    call_command("export_from_v1", "--skip_user", "--skip_ia")
    assert CountryGroup.objects.filter(country_group_id__in=["A", "B", "C"]).count() == 3
