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
from data_migration.queries import files as q_f
from data_migration.queries import import_application as q_ia
from data_migration.queries import user as q_u
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
        (dm.Office, web.Office),
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
        (dm.FirearmsAuthority, web.FirearmsAuthority),
        (dm.Section5Authority, web.Section5Authority),
        (dm.Section5Clause, web.Section5Clause),
        (dm.SILApplication, web.SILApplication),
        (dm.SILChecklist, web.SILChecklist),
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
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "file": [(q_f, "fa_certificate_files", dm.FileCombined)],
        "import_application": [
            (q_u, "importers", dm.Importer),
            (q_u, "offices", dm.Office),
            (q_ia, "fa_authorities", dm.FirearmsAuthority),
            (q_ia, "fa_authority_linked_offices", dm.FirearmsAuthorityOffice),
            (q_ia, "section5_authorities", dm.Section5Authority),
            (q_ia, "section5_linked_offices", dm.Section5AuthorityOffice),
            (q_ia, "sil_checklist", dm.SILChecklist),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": sil_xml_parsers})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sil_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [
            (dm.Office, web.Importer, "offices"),
            (dm.FirearmsAuthorityOffice, web.FirearmsAuthority, "linked_offices"),
            (dm.FirearmsAuthorityFile, web.FirearmsAuthority, "files"),
            (dm.Section5AuthorityOffice, web.Section5Authority, "linked_offices"),
            (dm.Section5AuthorityFile, web.Section5Authority, "files"),
            (dm.SILUserSection5, web.SILApplication, "user_section5"),
        ]
    },
)
@mock.patch.object(cx_Oracle, "connect")
def test_import_sil_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_ref")

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
        created_by_id=2,
    )

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        folder = dm.FileFolder.objects.create(
            folder_type="IMP_APP_DOCUMENTS", app_model="silapplication"
        )

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
                created_by_id=2,
            )
            f2 = dm.File.objects.create(
                target=target2,
                filename="Test User Sec 5 2",
                content_type="pdf",
                file_size=50,
                path="test2",
                created_by_id=2,
            )

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=i + 1000,
            application_type=iat,
            created_by_id=2,
            last_updated_by_id=2,
            importer_id=2,
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
            "bought_from_details_xml": xml_data.import_contact_xml if i == 1 else None,
        }
        dm.SILApplication.objects.create(**sil_data)
        dm.SILSupplementaryInfo.objects.create(
            imad=ia,
            supplementary_report_xml=xml_data.sr_manual_xml_5_goods
            if i == 0
            else xml_data.sr_upload_xml,
        )

    call_command("extract_v1_xml")

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

    importers = web.Importer.objects.order_by("pk")
    assert importers.count() == 3
    assert importers[0].offices.count() == 0
    assert importers[1].offices.count() == 2
    assert importers[2].offices.count() == 1

    assert web.Office.objects.count() == 3
    office1, office2, office3 = web.Office.objects.all()

    assert office1.address_1 == "123 Test"
    assert office1.address_2 == "Test City"
    assert office1.address_3 is None
    assert office1.address_4 is None
    assert office1.address_5 is None

    assert office2.address_1 == "456 Test"
    assert office2.address_2 is None
    assert office2.address_3 is None
    assert office2.address_4 is None
    assert office2.address_5 is None

    assert office3.address_1 == "ABC Test"
    assert office3.address_2 == "Test Town"
    assert office3.address_3 == "Test City"
    assert office3.address_4 is None
    assert office3.address_5 is None

    fa_auth = web.FirearmsAuthority.objects.order_by("pk")
    assert fa_auth.count() == 2
    fa_auth1, fa_auth2 = fa_auth
    assert fa_auth1.linked_offices.count() == 2
    assert fa_auth1.files.count() == 1
    assert fa_auth2.linked_offices.count() == 1
    assert fa_auth2.files.count() == 2

    sec5_auth = web.Section5Authority.objects.order_by("pk")
    assert sec5_auth.count() == 2
    sec5_auth1, sec5_auth2 = sec5_auth
    assert sec5_auth1.linked_offices.count() == 2
    assert sec5_auth1.files.count() == 1
    assert sec5_auth2.linked_offices.count() == 1
    assert sec5_auth2.files.count() == 1

    sil1, sil2 = web.SILApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert sil1.checklist.authority_required == "yes"
    assert sil1.checklist.authority_received == "yes"
    assert sil1.checklist.authority_police == "n/a"
    assert sil1.checklist.quantities_within_authority_restrictions == "yes"
    assert sil1.checklist.authority_cover_items_listed == "yes"
    assert sil2.checklist.authority_required == "no"
    assert sil2.checklist.authority_received == "no"
    assert sil2.checklist.authority_police == "no"
    assert sil2.checklist.quantities_within_authority_restrictions == "no"
    assert sil2.checklist.authority_cover_items_listed == "no"

    assert sil1.user_section5.count() == 2
    assert sil1.user_section5.filter(pk__in=(f1.pk, f2.pk)).count() == 2
    assert sil2.user_section5.count() == 0

    assert sil1.importapplication_ptr.importcontact_set.count() == 0
    assert sil2.importapplication_ptr.importcontact_set.count() == 2
    ic = sil2.importapplication_ptr.importcontact_set.first()

    assert ic.entity == "legal"
    assert ic.first_name == "FIREARMS DEALER"
    assert ic.street == "123 FAKE ST"
    assert ic.dealer == "yes"

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


oil_xml_parsers = [
    xml_parser.ImportContactParser,
    xml_parser.OILSupplementaryReportParser,
    xml_parser.OILReportFirearmParser,
]

oil_data_source_target = {
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
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.OpenIndividualLicenceApplication, web.OpenIndividualLicenceApplication),
        (dm.ChecklistFirearmsOILApplication, web.ChecklistFirearmsOILApplication),
        (dm.OILSupplementaryInfo, web.OILSupplementaryInfo),
        (dm.OILSupplementaryReport, web.OILSupplementaryReport),
        (dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {"import_application": [(q_ia, "oil_checklist", dm.ChecklistFirearmsOILApplication)]},
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": oil_xml_parsers})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, oil_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, {"import_application": []})
@mock.patch.object(cx_Oracle, "connect")
def test_import_oil_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
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
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        folder = dm.FileFolder.objects.create(
            folder_type="IMP_APP_DOCUMENTS", app_model="openindividuallicenceapplication"
        )

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=i + 1000,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
            file_folder=folder,
        )

        dm.ImportApplicationLicence.objects.create(imad=ia, status="AB")

        oil_data = {
            "pk": pk,
            "imad": ia,
            "section1": True,
            "section2": i == 0,
            "bought_from_details_xml": xml_data.import_contact_xml if i == 1 else None,
        }
        dm.OpenIndividualLicenceApplication.objects.create(**oil_data)
        dm.OILSupplementaryInfo.objects.create(
            imad=ia,
            supplementary_report_xml=xml_data.sr_upload_xml if i == 0 else xml_data.sr_manual_xml,
        )

    call_command("export_from_v1", "--skip_ref", "--skip_user", "--skip_file")
    call_command("extract_v1_xml")

    oil1, oil2 = dm.OpenIndividualLicenceApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert oil1.section1 is True
    assert oil1.section2 is True
    assert oil2.section1 is True
    assert oil2.section2 is False

    call_command("import_v1_data")

    oil1, oil2 = web.OpenIndividualLicenceApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert oil1.checklist.authority_required == "yes"
    assert oil1.checklist.authority_received == "yes"
    assert oil1.checklist.authority_police == "n/a"
    assert oil2.checklist.authority_required == "no"
    assert oil2.checklist.authority_received == "no"
    assert oil2.checklist.authority_police == "no"

    assert oil1.section1 is True
    assert oil1.section2 is True
    assert oil2.section1 is True
    assert oil2.section2 is False

    assert oil1.importapplication_ptr.importcontact_set.count() == 0
    assert oil2.importapplication_ptr.importcontact_set.count() == 2
    ic = oil2.importapplication_ptr.importcontact_set.first()

    assert ic.entity == "legal"
    assert ic.first_name == "FIREARMS DEALER"
    assert ic.street == "123 FAKE ST"
    assert ic.dealer == "yes"

    assert oil1.supplementary_info.reports.count() == 1
    assert oil2.supplementary_info.reports.count() == 2


tex_data_source_target = {
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
        (dm.ImportApplication, web.ImportApplication),
        (dm.TextilesApplication, web.TextilesApplication),
        (dm.TextilesChecklist, web.TextilesChecklist),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {"import_application": [(q_ia, "textiles_checklist", dm.TextilesChecklist)]},
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, tex_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, {"import_application": []})
@mock.patch.object(cx_Oracle, "connect")
def test_import_textiles_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    user_pk = max(web.User.objects.count(), dm.User.objects.count()) + 1
    dm.User.objects.create(id=user_pk, username="test_user")

    importer_pk = max(web.Importer.objects.count(), dm.Importer.objects.count()) + 1
    dm.Importer.objects.create(id=importer_pk, name="test_org", type="ORGANISATION")

    factory.CountryFactory(id=1000, name="My Test Country")
    cg = dm.CountryGroup.objects.create(country_group_id="TEX", name="TEX")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 3))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg, type="TEX")

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        folder = dm.FileFolder.objects.create(
            folder_type="IMP_APP_DOCUMENTS", app_model="textilesapplication"
        )

        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=1234 + i,
            application_type=iat,
            created_by_id=user_pk,
            last_updated_by_id=user_pk,
            importer_id=importer_pk,
            file_folder=folder,
        )

        dm.ImportApplicationLicence.objects.create(imad=ia, status="TX TEST")
        dm.TextilesApplication.objects.create(imad=ia)

    call_command("export_from_v1", "--skip_ref", "--skip_user", "--skip_file")
    call_command("import_v1_data")

    tex1, tex2, tex3 = web.TextilesApplication.objects.filter(pk__in=pk_range).order_by("pk")
    assert tex1.checklist.case_update == "no"
    assert tex1.checklist.fir_required == "n/a"
    assert tex1.checklist.response_preparation is True
    assert tex1.checklist.authorisation is True

    assert tex2.checklist.case_update == "yes"
    assert tex2.checklist.fir_required == "no"
    assert tex2.checklist.response_preparation is True
    assert tex2.checklist.authorisation is False

    assert hasattr(tex3, "checklist") is False


sps_data_source_target = {
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
        (dm.ImportApplication, web.ImportApplication),
        (dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
        (dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_XML, {"import_application": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sps_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [
            (dm.SPSSupportingDoc, web.PriorSurveillanceApplication, "supporting_documents")
        ]
    },
)
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {"file": [(q_f, "sps_application_files", dm.FileCombined)]},
)
def test_import_sps_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()

    dm.User.objects.create(id=2, username="test_user")
    dm.Importer.objects.create(id=2, name="test_org", type="ORGANISATION")

    call_command("export_from_v1", "--skip_ref", "--skip_ia", "--skip_user")

    factory.CountryFactory(id=1000, name="My Test Country")
    cg = dm.CountryGroup.objects.create(country_group_id="SPS", name="SPS")

    process_pk = max(web.Process.objects.count(), dm.Process.objects.count()) + 1
    pk_range = list(range(process_pk, process_pk + 2))
    iat = factory.ImportApplicationTypeFactory(master_country_group=cg)

    for i, pk in enumerate(pk_range):
        process = factory.ProcessFactory(pk=pk, process_type=web.ProcessTypes.FA_SIL, ima_id=pk + 7)
        ia = factory.ImportApplicationFactory(
            pk=pk,
            ima=process,
            status="COMPLETE",
            imad_id=i + 1000,
            application_type=iat,
            created_by_id=2,
            last_updated_by_id=2,
            importer_id=2,
            file_folder_id=i + 100,
        )

        dm.ImportApplicationLicence.objects.create(imad=ia, status="AC")

        dm.PriorSurveillanceContractFile.objects.create(
            imad=ia,
            file_type="PRO_FORMA_INVOICE" if i == 0 else "SUPPLY_CONTRACT",
            target_id=i + 1000,
        )
        sps_data = {
            "pk": pk,
            "imad": ia,
            "quantity": "NONSENSE" if i == 0 else 100,
            "value_gbp": "NONSENSE" if i == 0 else 100,
            "value_eur": "NONSENSE" if i == 0 else 100,
        }
        dm.PriorSurveillanceApplication.objects.create(**sps_data)

    call_command("import_v1_data")

    assert web.PriorSurveillanceApplication.objects.count() == 2
    assert web.PriorSurveillanceContractFile.objects.count() == 2

    sps1, sps2 = web.PriorSurveillanceApplication.objects.order_by("pk").all()

    assert sps1.contract_file.file_type == "pro_forma_invoice"
    assert sps1.supporting_documents.count() == 2
    assert sps1.quantity is None
    assert sps1.value_gbp is None
    assert sps1.value_eur is None

    assert sps2.contract_file.file_type == "supply_contract"
    assert sps2.supporting_documents.count() == 1
    assert sps2.quantity == 100
    assert sps2.value_gbp == 100
    assert sps2.value_eur == 100
