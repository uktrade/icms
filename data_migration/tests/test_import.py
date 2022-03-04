from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from data_migration import models as dm
from data_migration.queries import DATA_TYPE_M2M, DATA_TYPE_SOURCE_TARGET
from web import models as web

from .factory import (
    ImportApplicationFactory,
    ImportApplicationTypeFactory,
    ProcessFactory,
    WoodQuotaApplicationFactory,
)


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


ref_data_source_target = {
    "reference": [(dm.Country, web.Country), (dm.CountryGroup, web.CountryGroup)]
}
ref_m2m = {"reference": [(dm.CountryGroupCountry, web.CountryGroup, "countries")]}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, ref_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, ref_m2m)
def test_import_ref_data():
    last_c = web.Country.objects.order_by("pk").last()
    c_pk = (last_c and last_c.pk + 1) or 1
    c1 = dm.Country.objects.create(
        id=c_pk,
        name="A",
        status="ACTIVE",
        type="SOVEREIGN_TERRITORY",
        commission_code="A",
        hmrc_code="A",
    )
    c2 = dm.Country.objects.create(
        id=c_pk + 1,
        name="B",
        status="INACTIVE",
        type="SYSTEM",
        commission_code="B",
        hmrc_code="B",
    )

    last_cg = web.CountryGroup.objects.order_by("pk").last()
    cg_pk = (last_cg and last_cg.pk + 1) or 1
    cg1 = dm.CountryGroup.objects.create(id=cg_pk, country_group_id="A", name="A")
    cg2 = dm.CountryGroup.objects.create(id=cg_pk + 1, country_group_id="B", name="B")
    cg3 = dm.CountryGroup.objects.create(id=cg_pk + 2, country_group_id="C", name="C")

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

    call_command("import_v1_data", "--skip_user", "--skip_ia", "--skip_task")
    assert web.CountryGroup.objects.filter(name__in=["A", "B", "C"]).count() == 3
    assert web.CountryGroup.objects.get(name="A").countries.count() == 1
    assert web.CountryGroup.objects.get(name="B").countries.count() == 2
    assert web.CountryGroup.objects.get(name="C").countries.count() == 1


ia_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
    ],
    "reference": [
        (dm.CountryGroup, web.CountryGroup),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.WoodQuotaApplication, web.WoodQuotaApplication),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, ia_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, {"reference": []})
def test_import_wood_application_data():
    user_pk = max(web.User.objects.count(), dm.User.objects.count()) + 1
    dm.User.objects.create(id=user_pk, username="test_user")

    importer_pk = max(web.Importer.objects.count(), dm.Importer.objects.count()) + 1
    dm.Importer.objects.create(id=importer_pk, name="test_org", type="ORGANISATION")

    cg = dm.CountryGroup.objects.create(country_group_id="WD", name="WD")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 6))
    iat = ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = ProcessFactory(pk=pk, process_type=web.ProcessTypes.WOOD, ima_id=pk)

        if i < 3:
            status = "IN_PROGRESS"
        elif i < 4:
            status = "SUBMITTED"
        elif i < 5:
            status = "PROCESSING"
        else:
            status = "COMPLETE"

        ia = ImportApplicationFactory(
            pk=pk,
            ima=process,
            status=status,
            imad_id=pk,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
        )
        WoodQuotaApplicationFactory(pk=pk, imad=ia)

    call_command("import_v1_data")

    assert web.Process.objects.filter(id__in=pk_range).count() == 6
    assert web.ImportApplication.objects.filter(id__in=pk_range).count() == 6
    assert web.WoodQuotaApplication.objects.filter(id__in=pk_range).count() == 6
    assert web.Task.objects.filter(process_id__in=pk_range, task_type="prepare").count() == 3
    assert web.Task.objects.filter(process_id__in=pk_range, task_type="process").count() == 2
