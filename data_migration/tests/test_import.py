from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration import models as dm
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_SOURCE_TARGET,
)
from web import models as web

from . import utils


@override_settings(ALLOW_DATA_MIGRATION=False)
def test_data_import_not_enabled():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("import_v1_data")


ref_data_source_target = {
    "reference": [(dm.Country, web.Country), (dm.CountryGroup, web.CountryGroup)]
}
ref_m2m = {"reference": [(dm.CountryGroupCountry, web.CountryGroup, "countries")]}


@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, ref_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, ref_m2m)
def test_import_ref_data(dummy_dm_settings):
    last_c = web.Country.objects.order_by("pk").last()
    c_pk = (last_c and last_c.pk + 1) or 1
    c1 = dm.Country.objects.create(
        id=c_pk,
        name="A",
        is_active=1,
        type="SOVEREIGN_TERRITORY",
        commission_code="A",
        hmrc_code="A",
    )
    c2 = dm.Country.objects.create(
        id=c_pk + 1,
        name="B",
        is_active=0,
        type="SYSTEM",
        commission_code="B",
        hmrc_code="B",
    )

    last_cg = web.CountryGroup.objects.order_by("pk").last()
    cg_pk = (last_cg and last_cg.pk + 1) or 1
    cg1 = dm.CountryGroup.objects.create(
        id=cg_pk, country_group_id="CFS", name="Certificate of Free Sale Countries"
    )
    cg2 = dm.CountryGroup.objects.create(
        id=cg_pk + 1, country_group_id="COM", name="Certificate of Manufacture Countries"
    )
    cg3 = dm.CountryGroup.objects.create(
        id=cg_pk + 2, country_group_id="GMP", name="Goods Manufacturing Practice Countries"
    )

    last_cgc = web.CountryGroup.countries.through.objects.order_by("pk").last()
    cgc_pk = (last_cgc and last_cgc.pk + 1) or 1
    dm.CountryGroupCountry.objects.bulk_create(
        [
            dm.CountryGroupCountry(id=pk, country=c, countrygroup=cg)
            for pk, c, cg in [
                (cgc_pk, c1, cg1),
                (cgc_pk + 1, c1, cg2),
                (cgc_pk + 2, c2, cg2),
                (cgc_pk + 3, c2, cg3),
            ]
        ]
    )

    call_command("import_v1_data", "--skip_user", "--skip_ia", "--skip_task", "--skip_file")
    assert web.CountryGroup.objects.filter(name__in=["CFS", "COM", "GMP"]).count() == 3
    assert web.CountryGroup.objects.get(name="CFS").countries.count() == 1
    assert web.CountryGroup.objects.get(name="COM").countries.count() == 2
    assert web.CountryGroup.objects.get(name="GMP").countries.count() == 1


start_test_source_target = {
    "user": [],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.Constabulary, web.Constabulary),
    ],
    "import_application": [
        (dm.Unit, web.Unit),
        (dm.ObsoleteCalibreGroup, web.ObsoleteCalibreGroup),
    ],
    "file": [],
}


start_test_data_m2m = {
    "reference": [
        (
            dm.CountryGroupCountry,
            web.CountryGroup,
            "countries",
        ),
    ],
    "import_application": [],
    "file": [],
}


@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, start_test_source_target)
@mock.patch.dict(DATA_TYPE_M2M, start_test_data_m2m)
def test_start_reference_1(dummy_dm_settings):
    utils.create_test_dm_models()
    call_command("import_v1_data", "--start=reference.1")
    assert web.Country.objects.count() == 4
    assert web.CountryGroup.objects.count() == 3
    assert web.CountryGroup.countries.through.objects.count() == 5
    assert web.Constabulary.objects.count() == 3
    assert web.Unit.objects.count() == 3
    assert web.ObsoleteCalibreGroup.objects.count() == 3


@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, start_test_source_target)
@mock.patch.dict(DATA_TYPE_M2M, start_test_data_m2m)
def test_start_import_application_1(dummy_dm_settings):
    utils.create_test_dm_models()
    call_command("import_v1_data", "--start=import_application.1")
    assert web.Country.objects.count() == 0
    assert web.CountryGroup.objects.count() == 0
    assert web.CountryGroup.countries.through.objects.count() == 0
    assert web.Constabulary.objects.count() == 0
    assert web.Unit.objects.count() == 3
    assert web.ObsoleteCalibreGroup.objects.count() == 3


@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, start_test_source_target)
@mock.patch.dict(DATA_TYPE_M2M, start_test_data_m2m)
def test_start_ref_2(dummy_dm_settings):
    utils.create_test_dm_models()
    call_command("import_v1_data", "--start=ia.2")
    assert web.Country.objects.count() == 0
    assert web.CountryGroup.objects.count() == 0
    assert web.CountryGroup.countries.through.objects.count() == 0
    assert web.Constabulary.objects.count() == 0
    assert web.Unit.objects.count() == 0
    assert web.ObsoleteCalibreGroup.objects.count() == 3
