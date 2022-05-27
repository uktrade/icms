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
from data_migration.utils import xml_parser
from web import models as web

from . import factory, utils, xml_data

sil_xml_parsers = [
    xml_parser.ImportContactParser,
    xml_parser.SILGoodsParser,
    xml_parser.SILSupplementaryReportParser,
    xml_parser.SILReportFirearmParser,
]

sil_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.ObsoleteCalibreGroup, web.ObsoleteCalibreGroup),
        (dm.ObsoleteCalibre, web.ObsoleteCalibre),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.Section5Clause, web.Section5Clause),
        (dm.SILApplication, web.SILApplication),
        (dm.SILUserSection5, web.SILUserSection5),
        (dm.SILGoodsSection1, web.SILGoodsSection1),
        (dm.SILGoodsSection2, web.SILGoodsSection2),
        (dm.SILGoodsSection5, web.SILGoodsSection5),
        (dm.SILGoodsSection582Obsolete, web.SILGoodsSection582Obsolete),  # /PS-IGNORE
        (dm.SILGoodsSection582Other, web.SILGoodsSection582Other),  # /PS-IGNORE
        (dm.SILSupplementaryInfo, web.SILSupplementaryInfo),
        (dm.SILSupplementaryReport, web.SILSupplementaryReport),
        (dm.SILSupplementaryReportFirearmSection1, web.SILSupplementaryReportFirearmSection1),
        (dm.SILSupplementaryReportFirearmSection2, web.SILSupplementaryReportFirearmSection2),
        (dm.SILSupplementaryReportFirearmSection5, web.SILSupplementaryReportFirearmSection5),
        (
            dm.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
        ),
        (
            dm.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        ),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, {"import_application": [], "file": []})
@mock.patch.dict(DATA_TYPE_XML, {"import_application": sil_xml_parsers})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sil_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {"import_application": [(dm.SILUserSection5, web.SILApplication, "user_section5")]},
)
@mock.patch.object(cx_Oracle, "connect")
def test_import_sil_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    user_pk = max(web.User.objects.count(), dm.User.objects.count()) + 1
    dm.User.objects.create(id=user_pk, username="test_user")

    importer_pk = max(web.Importer.objects.count(), dm.Importer.objects.count()) + 1
    dm.Importer.objects.create(id=importer_pk, name="test_org", type="ORGANISATION")

    factory.CountryFactory(id=1000, name="My Test Country")
    cg = dm.CountryGroup.objects.create(country_group_id="SIL", name="SIL")

    ocg = dm.ObsoleteCalibreGroup.objects.create(name="Test OC Group", order=1, legacy_id=1)
    dm.ObsoleteCalibre.objects.create(legacy_id=444, calibre_group=ocg, name="Test OC", order=1)

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 2))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    dm.Section5Clause.objects.create(
        clause="Test Clause",
        legacy_code="5_1_ABA",
        description="Test Description",
        created_by_id=user_pk,
    )

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        folder = dm.FileFolder.objects.create(folder_type="IMP_APP_DOCUMENTS")

        if i == 0:
            target1 = dm.FileTarget.objects.create(
                folder=folder, target_type="IMP_SECTION5_AUTHORITY"
            )
            target2 = dm.FileTarget.objects.create(
                folder=folder, target_type="IMP_SECTION5_AUTHORITY"
            )
            f1 = dm.File.objects.create(
                target=target1,
                filename="Test User Sec 5",
                content_type="pdf",
                file_size=100,
                path="test",
                created_by_id=user_pk,
            )
            f2 = dm.File.objects.create(
                target=target2,
                filename="Test User Sec 5 2",
                content_type="pdf",
                file_size=50,
                path="test2",
                created_by_id=user_pk,
            )

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=pk + 7,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
            file_folder=folder,
        )

        dm.ImportApplicationLicence.objects.create(imad=ia, status="AC")

        sil_data = {
            "pk": pk,
            "imad": ia,
            "commodities_xml": xml_data.sil_goods if i == 0 else xml_data.sil_goods_sec_1,
            "section1": True,
            "section2": i == 0,
            "section5": i == 0,
            "section58_obsolete": i == 0,
            "section58_other": i == 0,
            "bought_from_details_xml": xml_data.import_contact_xml,
        }
        dm.SILApplication.objects.create(**sil_data)
        dm.SILSupplementaryInfo.objects.create(
            imad=ia,
            supplementary_report_xml=xml_data.sr_manual_xml_5_goods
            if i == 0
            else xml_data.sr_upload_xml,
        )

    call_command("export_from_v1", "--skip_ref", "--skip_user")

    # Get the personal / sensitive ignores out the way
    dmGoodsObsolete = dm.SILGoodsSection582Obsolete  # /PS-IGNORE
    dmGoodsOther = dm.SILGoodsSection582Other  # /PS-IGNORE
    dmRFObsolete = dm.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
    dmRFOther = dm.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE
    webRFObsolete = web.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
    webRFOther = web.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE

    sil1, sil2 = dm.SILApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert dm.SILGoodsSection1.objects.filter(import_application=sil1).count() == 1
    assert dm.SILGoodsSection1.objects.filter(import_application=sil2).count() == 1
    assert dm.SILGoodsSection2.objects.filter(import_application=sil1).count() == 1
    assert dm.SILGoodsSection5.objects.filter(import_application=sil1).count() == 1
    assert dmGoodsObsolete.objects.filter(import_application=sil1).count() == 1
    assert dmGoodsOther.objects.filter(import_application=sil1).count() == 1

    sil1_f = {"report__supplementary_info__imad": sil1.imad}
    sil2_f = {"report__supplementary_info__imad": sil2.imad}

    assert dm.SILSupplementaryReportFirearmSection1.objects.filter(**sil1_f).count() == 2
    assert dm.SILSupplementaryReportFirearmSection1.objects.filter(**sil2_f).count() == 1
    assert dm.SILSupplementaryReportFirearmSection2.objects.filter(**sil1_f).count() == 1
    assert dm.SILSupplementaryReportFirearmSection5.objects.filter(**sil1_f).count() == 2
    assert dmRFObsolete.objects.filter(**sil1_f).count() == 1
    assert dmRFOther.objects.filter(**sil1_f).count() == 2

    call_command("import_v1_data")

    sil1, sil2 = web.SILApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert sil1.user_section5.count() == 2
    assert sil1.user_section5.filter(pk__in=(f1.pk, f2.pk)).count() == 2
    assert sil2.user_section5.count() == 0

    sil1_f = {"import_application_id": sil1.pk}
    sil2_f = {"import_application_id": sil2.pk}

    assert web.SILGoodsSection1.objects.filter(**sil1_f).count() == 1
    assert web.SILGoodsSection1.objects.filter(**sil2_f).count() == 1
    assert web.SILGoodsSection2.objects.filter(**sil1_f).count() == 1
    assert web.SILGoodsSection5.objects.filter(**sil1_f).count() == 1
    sec5 = web.SILGoodsSection5.objects.filter(**sil1_f).first()
    assert sec5.subsection == "Test Description"
    assert web.SILGoodsSection582Obsolete.objects.filter(**sil1_f).count() == 1  # /PS-IGNORE
    sil_oc = web.SILGoodsSection582Obsolete.objects.filter(**sil1_f).first()  # /PS-IGNORE
    assert sil_oc.obsolete_calibre == "Test OC"
    assert web.SILGoodsSection582Other.objects.filter(**sil1_f).count() == 1  # /PS-IGNORE

    oc = web.ObsoleteCalibre.objects.get(name="Test OC")
    assert oc.calibre_group.name == "Test OC Group"

    sil1_f = {"goods_certificate__import_application_id": sil1.pk}
    sil2_f = {"goods_certificate__import_application_id": sil2.pk}

    assert web.SILSupplementaryReportFirearmSection1.objects.filter(**sil1_f).count() == 2
    assert web.SILSupplementaryReportFirearmSection1.objects.filter(**sil2_f).count() == 1
    assert web.SILSupplementaryReportFirearmSection2.objects.filter(**sil1_f).count() == 1
    assert web.SILSupplementaryReportFirearmSection5.objects.filter(**sil1_f).count() == 2
    assert webRFObsolete.objects.filter(**sil1_f).count() == 1
    assert webRFOther.objects.filter(**sil1_f).count() == 2
