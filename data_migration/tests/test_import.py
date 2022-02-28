from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration.models import Country as C
from data_migration.models import CountryGroup as CG
from data_migration.models import CountryGroupCountry
from data_migration.queries import DATA_TYPE_M2M, DATA_TYPE_SOURCE_TARGET
from web.models import Country, CountryGroup


@override_settings(ALLOW_DATA_MIGRATION=False)
@override_settings(APP_ENV="production")
def test_data_import_not_enabled():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("import_v1_data")


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="test")
def test_data_import_not_enabled_non_prod():
    with pytest.raises(
        CommandError, match="Data migration has not been enabled for this environment"
    ):
        call_command("import_v1_data")


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, {"reference": [(C, Country), (CG, CountryGroup)]})
@mock.patch.dict(DATA_TYPE_M2M, {"reference": [(CountryGroupCountry, CountryGroup, "countries")]})
def test_export_data():
    last_c = Country.objects.order_by("pk").last()
    c_pk = (last_c and last_c.pk + 1) or 1
    c1 = C.objects.create(
        id=c_pk,
        name="A",
        status="ACTIVE",
        type="SOVEREIGN_TERRITORY",
        commission_code="A",
        hmrc_code="A",
    )
    c2 = C.objects.create(
        id=c_pk + 1,
        name="B",
        status="INACTIVE",
        type="SYSTEM",
        commission_code="B",
        hmrc_code="B",
    )

    last_cg = CountryGroup.objects.order_by("pk").last()
    cg_pk = (last_cg and last_cg.pk + 1) or 1
    cg1 = CG.objects.create(id=cg_pk, country_group_id="A", name="A")
    cg2 = CG.objects.create(id=cg_pk + 1, country_group_id="B", name="B")
    cg3 = CG.objects.create(id=cg_pk + 2, country_group_id="C", name="C")

    last_cgc = CountryGroup.countries.through.objects.order_by("pk").last()
    cgc_pk = (last_cgc and last_cgc.pk + 1) or 1
    CountryGroupCountry.objects.bulk_create(
        [
            CountryGroupCountry(id=pk, country=c, countrygroup=cg)
            for pk, c, cg in [
                (cgc_pk, c1, cg1),
                (cgc_pk + 1, c1, cg2),
                (cgc_pk + 2, c2, cg2),
                (cgc_pk + 3, c2, cg3),
            ]
        ]
    )

    call_command("import_v1_data", "--skip_user", "--skip_ia")
    assert CountryGroup.objects.filter(name__in=["A", "B", "C"]).count() == 3
    assert CountryGroup.objects.get(name="A").countries.count() == 1
    assert CountryGroup.objects.get(name="B").countries.count() == 2
    assert CountryGroup.objects.get(name="C").countries.count() == 1
