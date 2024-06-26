from unittest import mock

import oracledb
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration import models, queries
from data_migration.management.commands.config.run_order import DATA_TYPE_QUERY_MODEL
from data_migration.management.commands.types import QueryModel

from . import utils


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
    assert (
        models.CountryGroup.objects.filter(
            country_group_id__in=["FA_SIL_COO", "FA_SIL_COC", "FA_OIL_COO"]
        ).count()
        == 3
    )


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
