from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from data_migration import models as dm
from data_migration.queries import DATA_TYPE_M2M, DATA_TYPE_SOURCE_TARGET
from web import models as web

from . import factory, xml_data


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
        (dm.ImportApplicationLicence, web.ImportApplicationLicence),
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
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.WOOD, ima_id=pk)
        if i < 3:
            status = "IN_PROGRESS"
        elif i < 4:
            status = "SUBMITTED"
        elif i < 5:
            status = "PROCESSING"
        else:
            status = "COMPLETE"

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status=status,
            imad_id=pk,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
        )

        if status == "COMPLETE":
            dm.ImportApplicationLicence.objects.create(imad=ia, status="AC")

        factory.WoodQuotaApplicationFactory(pk=pk, imad=ia)

    call_command("import_v1_data")

    assert web.Process.objects.filter(id__in=pk_range).count() == 6
    assert web.ImportApplication.objects.filter(id__in=pk_range).count() == 6
    assert web.WoodQuotaApplication.objects.filter(id__in=pk_range).count() == 6
    assert (
        web.ImportApplicationLicence.objects.filter(
            import_application_id__in=pk_range, status="DR"
        ).count()
        == 5
    )
    assert (
        web.ImportApplicationLicence.objects.filter(
            import_application_id__in=pk_range, status="AC"
        ).count()
        == 1
    )
    assert web.Task.objects.filter(process_id__in=pk_range, task_type="prepare").count() == 3
    assert web.Task.objects.filter(process_id__in=pk_range, task_type="process").count() == 2


oil_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.Constabulary, web.Constabulary),
        (dm.File, web.File),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.OpenIndividualLicenceApplication, web.OpenIndividualLicenceApplication),
        (dm.OILSupplementaryInfo, web.OILSupplementaryInfo),
        (dm.OILSupplementaryReport, web.OILSupplementaryReport),
        (dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
        (dm.UserImportCertificate, web.UserImportCertificate),
    ],
}

oil_data_m2m = {
    "import_application": [
        (
            dm.UserImportCertificate,
            web.OpenIndividualLicenceApplication,
            "user_imported_certificates",
        )
    ]
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, oil_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, oil_data_m2m)
def test_import_oil_data():
    user_pk = max(web.User.objects.count(), dm.User.objects.count()) + 1
    dm.User.objects.create(id=user_pk, username="test_user")
    importer_pk = max(web.Importer.objects.count(), dm.Importer.objects.count()) + 1
    dm.Importer.objects.create(id=importer_pk, name="test_org", type="ORGANISATION")
    factory.CountryFactory(id=1000, name="My Test Country")
    cg = dm.CountryGroup.objects.create(country_group_id="OIL", name="OIL")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 2))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_OIL, ima_id=pk + 7)
        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="IN_PROGRESS",
            imad_id=pk + 7,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
            submit_datetime=None if i == 0 else timezone.now(),
        )
        dm.ImportApplicationLicence.objects.create(imad=ia, status="AC")
        factory.OILApplicationFactory(pk=pk, imad=ia)
        dm.ImportContact.objects.bulk_create(
            dm.ImportContact.parse_xml([(pk, xml_data.import_contact_xml)])
        )

        if i == 0:
            sr = factory.OILSupplementaryInfoFactory(
                imad=ia, supplementary_report_xml=xml_data.sr_upload_xml
            )
            dm.OILSupplementaryReport.objects.bulk_create(
                dm.OILSupplementaryReport.parse_xml([(sr.pk, xml_data.sr_upload_xml)])
            )
            ft1 = dm.FileTarget.objects.create()
            factory.UserImportCertificateFactory(
                target=ft1, import_application=ia, certificate_type="registered"
            )
            ft2 = dm.FileTarget.objects.create()
            factory.FileFactory(created_by_id=user_pk, target=ft2)
            factory.UserImportCertificateFactory(
                target=ft2, import_application=ia, certificate_type="registered", expiry_date=None
            )
            ft3 = dm.FileTarget.objects.create()
            factory.FileFactory(created_by_id=user_pk, target=ft3)
            factory.UserImportCertificateFactory(
                target=ft3, import_application=ia, certificate_type="registered", constabulary=None
            )
            ft4 = dm.FileTarget.objects.create()
            factory.FileFactory(created_by_id=user_pk, target=ft4)
            factory.UserImportCertificateFactory(
                target=ft4, import_application=ia, certificate_type="registered", reference=None
            )
            ft5 = dm.FileTarget.objects.create()
            factory.FileFactory(created_by_id=user_pk, target=ft5)
            factory.UserImportCertificateFactory(
                target=ft5, import_application=ia, certificate_type="registered", reference="ABC"
            )
        else:
            ft = dm.FileTarget.objects.create()
            factory.FileFactory(created_by_id=user_pk, target=ft)

            factory.UserImportCertificateFactory(
                target=ft, import_application=ia, certificate_type="registered"
            )
            si = factory.OILSupplementaryInfoFactory(
                imad=ia, supplementary_report_xml=xml_data.sr_manual_xml
            )
            dm.OILSupplementaryReport.objects.bulk_create(
                dm.OILSupplementaryReport.parse_xml([(si.pk, xml_data.sr_manual_xml)])
            )
            sr = dm.OILSupplementaryReport.objects.order_by("-pk").first()
            dm.OILSupplementaryReportFirearm.objects.create(
                report=sr,
                is_manual=True,
                goods_certificate_legacy_id=1,
                serial_number=i,
                model=i,
                calibre=i,
            )

    call_command("import_v1_data")

    oil_apps = web.OpenIndividualLicenceApplication.objects.filter(pk__in=pk_range)
    assert oil_apps.count() == 2

    oil1, oil2 = oil_apps

    oil1_ic = oil1.importcontact_set.all()
    assert oil1_ic.count() == 2

    oil2_ic = oil2.importcontact_set.all()
    assert oil2_ic.count() == 2

    oil1_sr = oil1.supplementary_info.reports.all()
    assert oil1_sr.count() == 1

    (oil1_sr,) = oil1_sr
    assert oil1_sr.transport == "AIR"
    assert oil1_ic.filter(pk=oil1_sr.bought_from_id).exists()

    oil2_sr = oil2.supplementary_info.reports.all()
    assert oil2_sr.count() == 2

    oil2_sr1, oil2_sr2 = oil2_sr.order_by("bought_from_id")

    assert oil2_ic.filter(pk=oil2_sr1.bought_from_id).exists()
    assert oil2_sr2.bought_from_id is None

    assert oil1.user_imported_certificates.count() == 1
    assert oil1.user_imported_certificates.filter(reference="ABC").count() == 1
    assert oil2.user_imported_certificates.count() == 1


dfl_data_source_target = {
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
        (dm.File, web.File),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.DFLApplication, web.DFLApplication),
        (dm.DFLGoodsCertificate, web.DFLGoodsCertificate),
        (dm.DFLSupplementaryInfo, web.DFLSupplementaryInfo),
        (dm.DFLSupplementaryReport, web.DFLSupplementaryReport),
        (dm.DFLSupplementaryReportFirearm, web.DFLSupplementaryReportFirearm),
    ],
}


dfl_data_m2m = {
    "import_application": [
        (
            dm.DFLGoodsCertificate,
            web.DFLApplication,
            "goods_certificates",
        )
    ]
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, dfl_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, dfl_data_m2m)
def test_import_dfl_data():
    user_pk = max(web.User.objects.count(), dm.User.objects.count()) + 1
    dm.User.objects.create(id=user_pk, username="test_user")

    importer_pk = max(web.Importer.objects.count(), dm.Importer.objects.count()) + 1
    dm.Importer.objects.create(id=importer_pk, name="test_org", type="ORGANISATION")

    c = factory.CountryFactory(id=1000, name="My Test Country")

    cg = dm.CountryGroup.objects.create(country_group_id="DFL", name="DFL")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 2))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.WOOD, ima_id=pk + 7)

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=pk + 7,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
        )

        dm.ImportApplicationLicence.objects.create(imad=ia, status="AC")

        dfl = factory.DFLApplicationFactory(pk=pk, imad=ia)
        dm.ImportContact.objects.bulk_create(
            dm.ImportContact.parse_xml([(pk, xml_data.import_contact_xml)])
        )
        ft = dm.FileTarget.objects.create()
        factory.FileFactory(created_by_id=user_pk, target=ft)
        factory.DFLGoodsCertificateFactory(
            target=ft, dfl_application=dfl, legacy_id=1, issuing_country=c
        )
        si = factory.DFLSupplementaryInfoFactory(imad=ia)
        sr = dm.DFLSupplementaryReport.objects.create(
            supplementary_info=si,
            transport="AIR",
            date_received=timezone.datetime(2020, 1, 1).date(),
            bought_from_legacy_id=1,
        )
        dm.DFLSupplementaryReportFirearm.objects.create(
            report=sr,
            is_manual=True,
            goods_certificate_legacy_id=1,
            serial_number=i,
            model=i,
            calibre=i,
        )

    call_command("import_v1_data")

    dfl_apps = web.DFLApplication.objects.filter(pk__in=pk_range)
    assert dfl_apps.count() == 2

    dfl1, dfl2 = dfl_apps

    assert dfl1.goods_certificates.count() == 1
    assert dfl2.goods_certificates.count() == 1

    gc1 = dfl1.goods_certificates.first()
    gc2 = dfl2.goods_certificates.first()

    sr1 = dfl1.supplementary_info.reports.all()
    assert sr1.count() == 1
    assert sr1.first().firearms.count() == 1

    rf1 = sr1.first().firearms.first()
    assert rf1.goods_certificate == gc1

    sr2 = dfl2.supplementary_info.reports.all()
    assert sr2.count() == 1
    assert sr2.first().firearms.count() == 1

    rf2 = sr2.first().firearms.first()
    assert rf2.goods_certificate == gc2
