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
from data_migration.queries import export_application as q_ex
from data_migration.queries import files as q_f
from data_migration.queries import import_application as q_ia
from data_migration.queries import reference as q_ref
from data_migration.queries import user as q_u
from data_migration.utils import xml_parser
from web import models as web

from . import factory, utils, xml_data

sil_xml_parsers = [
    xml_parser.ImportContactParser,
    xml_parser.SILGoodsParser,
    xml_parser.SILSupplementaryReportParser,
    xml_parser.SILReportFirearmParser,
    xml_parser.VariationImportParser,
]

sil_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Exporter, web.Exporter),
        (dm.Office, web.Office),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.ObsoleteCalibreGroup, web.ObsoleteCalibreGroup),
        (dm.ObsoleteCalibre, web.ObsoleteCalibre),
        (dm.CommodityType, web.CommodityType),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportApplicationLicence, web.ImportApplicationLicence),
        (dm.CaseEmail, web.CaseEmail),
        (dm.CaseNote, web.CaseNote),
        (dm.EndorsementImportApplication, web.EndorsementImportApplication),
        (dm.FurtherInformationRequest, web.FurtherInformationRequest),
        (dm.UpdateRequest, web.UpdateRequest),
        (dm.VariationRequest, web.VariationRequest),
        (dm.ImportCaseDocument, web.CaseDocumentReference),
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
        (dm.SILLegacyGoods, web.SILLegacyGoods),
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
        (
            dm.SILSupplementaryReportFirearmSectionLegacy,
            web.SILSupplementaryReportFirearmSectionLegacy,
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
        "reference": [
            (q_ref, "country", dm.Country),
            (q_ref, "country_group", dm.CountryGroup),
            (q_ref, "commodity_type", dm.CommodityType),
        ],
        "file": [
            (q_f, "case_note_files", dm.FileCombined),
            (q_f, "fir_files", dm.FileCombined),
            (q_f, "sil_application_files", dm.FileCombined),
            (q_f, "fa_certificate_files", dm.FileCombined),
        ],
        "import_application": [
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
            (q_u, "exporters", dm.Exporter),
            (q_u, "exporter_offices", dm.Office),
            (q_ia, "ia_type", dm.ImportApplicationType),
            (q_ia, "sil_application", dm.SILApplication),
            (q_ia, "ia_licence", dm.ImportApplicationLicence),
            (q_ia, "ia_licence_docs", dm.CaseDocument),
            (q_ia, "fa_authorities", dm.FirearmsAuthority),
            (q_ia, "fa_authority_linked_offices", dm.FirearmsAuthorityOffice),
            (q_ia, "section5_authorities", dm.Section5Authority),
            (q_ia, "section5_linked_offices", dm.Section5AuthorityOffice),
            (q_ia, "sil_checklist", dm.SILChecklist),
            (q_ia, "constabulary_emails", dm.CaseEmail),
            (q_ia, "case_note", dm.CaseNote),
            (q_ia, "update_request", dm.UpdateRequest),
            (q_ia, "fir", dm.FurtherInformationRequest),
            (q_ia, "endorsement", dm.EndorsementImportApplication),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": sil_xml_parsers})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, sil_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [
            (dm.CaseNote, web.ImportApplication, "case_notes"),
            (dm.CaseNoteFile, web.CaseNote, "files"),
            (dm.VariationRequest, web.ImportApplication, "variation_requests"),
            (dm.CaseEmail, web.ImportApplication, "case_emails"),
            (dm.UpdateRequest, web.ImportApplication, "update_requests"),
            (dm.FurtherInformationRequest, web.ImportApplication, "further_information_requests"),
            (dm.FIRFile, web.FurtherInformationRequest, "files"),
            (dm.Office, web.Importer, "offices"),
            (dm.Office, web.Exporter, "offices"),
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
    ocg = dm.ObsoleteCalibreGroup.objects.create(name="Test OC Group", order=1, legacy_id=1)
    dm.ObsoleteCalibre.objects.create(legacy_id=444, calibre_group=ocg, name="Test OC", order=1)

    call_command("export_from_v1", "--skip_export")

    dm.Section5Clause.objects.create(
        clause="Test Clause",
        legacy_code="5_1_ABA",
        description="Test Description",
        created_by_id=2,
    )

    call_command("extract_v1_xml", "--skip_export")

    # Get the personal / sensitive ignores out the way
    dmGoodsObsolete = dm.SILGoodsSection582Obsolete  # /PS-IGNORE
    dmGoodsOther = dm.SILGoodsSection582Other  # /PS-IGNORE
    dmRFObsolete = dm.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
    dmRFOther = dm.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE
    webRFObsolete = web.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
    webRFOther = web.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE

    assert dm.SILApplication.objects.count() == 3
    sil1, sil2, sil3 = dm.SILApplication.objects.order_by("pk")

    assert dm.SILGoodsSection1.objects.filter(import_application=sil1).count() == 1
    assert dm.SILGoodsSection1.objects.filter(import_application=sil2).count() == 1
    assert dm.SILGoodsSection2.objects.filter(import_application=sil1).count() == 1
    assert dm.SILGoodsSection5.objects.filter(import_application=sil1).count() == 1
    assert dmGoodsObsolete.objects.filter(import_application=sil1).count() == 1
    assert dmGoodsOther.objects.filter(import_application=sil1).count() == 1
    assert dm.SILLegacyGoods.objects.filter(import_application=sil3).count() == 2

    sil1_f = {"report__supplementary_info__imad": sil1.imad}
    sil2_f = {"report__supplementary_info__imad": sil2.imad}
    sil3_f = {"report__supplementary_info__imad": sil3.imad}

    assert dm.SILSupplementaryReportFirearmSection1.objects.filter(**sil1_f).count() == 2
    assert dm.SILSupplementaryReportFirearmSection1.objects.filter(**sil2_f).count() == 1
    assert dm.SILSupplementaryReportFirearmSection2.objects.filter(**sil1_f).count() == 1
    assert dm.SILSupplementaryReportFirearmSection5.objects.filter(**sil1_f).count() == 2
    assert dmRFObsolete.objects.filter(**sil1_f).count() == 1
    assert dmRFOther.objects.filter(**sil1_f).count() == 2
    assert dm.SILSupplementaryReportFirearmSectionLegacy.objects.filter(**sil3_f).count() == 2

    call_command("import_v1_data", "--skip_export")

    importers = web.Importer.objects.order_by("pk")
    assert importers.count() == 3
    assert importers[0].offices.count() == 0
    assert importers[1].offices.count() == 2
    assert importers[2].offices.count() == 1

    assert web.Office.objects.count() == 6
    office1, office2, office3 = web.Office.objects.filter(importer__isnull=False).order_by("pk")

    assert office1.address_1 == "123 Test"
    assert office1.address_2 == "Test City"
    assert office1.address_3 is None
    assert office1.address_4 is None
    assert office1.address_5 is None
    assert office1.postcode == "ABC"

    assert office2.address_1 == "456 Test"
    assert office2.address_2 is None
    assert office2.address_3 is None
    assert office2.address_4 is None
    assert office2.address_5 is None
    assert office2.postcode == "DEF"

    assert office3.address_1 == "ABC Test"
    assert office3.address_2 == "Test Town"
    assert office3.address_3 == "Test City"
    assert office3.address_4 is None
    assert office3.address_5 is None
    assert office3.postcode == "TESTLONG"

    office4, office5, office6 = web.Office.objects.filter(exporter__isnull=False).order_by("pk")
    assert office4.address_1 == "123 Test"
    assert office4.address_2 == "Test City"
    assert office4.address_3 is None
    assert office4.address_4 is None
    assert office4.address_5 is None
    assert office4.postcode == "Exp A"

    assert office5.address_1 == "456 Test"
    assert office5.address_2 == "Very Long Postcode"
    assert office5.address_3 is None
    assert office5.address_4 is None
    assert office5.address_5 is None
    assert office5.postcode is None

    assert office6.address_1 == "ABC Test"
    assert office6.address_2 == "Test Town"
    assert office6.address_3 == "Test City"
    assert office6.address_4 is None
    assert office6.address_5 is None
    assert office6.postcode == "TEST"

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

    assert web.SILApplication.objects.count() == 3
    sil1, sil2, sil3 = web.SILApplication.objects.order_by("pk")

    assert sil1.licences.count() == 1
    assert sil2.licences.count() == 3
    assert sil2.licences.filter(status="AC").count() == 1

    l1 = sil1.licences.first()
    l2, l3, l4 = sil2.licences.all()

    assert l1.document_references.count() == 2
    assert l1.document_references.filter(document_type="LICENCE").count() == 1
    assert l1.document_references.filter(document_type="COVER_LETTER").count() == 1
    assert l2.document_references.count() == 3
    assert l2.document_references.filter(document_type="LICENCE").count() == 2
    assert l2.document_references.filter(document_type="COVER_LETTER").count() == 1
    assert l3.document_references.count() == 0
    assert l4.document_references.count() == 2

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
    assert sil1.user_section5.count() == 2
    assert sil2.user_section5.count() == 0

    ia1 = sil1.importapplication_ptr
    ia2 = sil2.importapplication_ptr

    assert ia1.importcontact_set.count() == 0
    assert ia2.importcontact_set.count() == 2
    ic = ia2.importcontact_set.first()

    assert ic.entity == "legal"
    assert ic.first_name == "FIREARMS DEALER"
    assert ic.street == "123 FAKE ST"
    assert ic.dealer == "yes"

    sil1_f = {"import_application_id": sil1.pk}
    sil2_f = {"import_application_id": sil2.pk}
    sil3_f = {"import_application_id": sil3.pk}

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

    assert web.SILLegacyGoods.objects.filter(**sil3_f).count() == 2
    lg1, lg2 = web.SILLegacyGoods.objects.filter(**sil3_f).order_by("pk")

    assert lg1.description == "Legacy Commodity"
    assert lg1.quantity == 25
    assert lg1.unlimited_quantity is False
    assert lg1.obsolete_calibre is None

    assert lg2.description == "Legacy Commodity OC"
    assert lg2.quantity is None
    assert lg2.unlimited_quantity is True
    assert lg2.obsolete_calibre == "Test OC"

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

    assert ia1.case_emails.count() == 3
    assert ia2.case_emails.count() == 0

    open_email = ia1.case_emails.get(status="OPEN")
    assert len(open_email.cc_address_list) == 2

    closed_email = ia1.case_emails.get(status="CLOSED")
    assert len(closed_email.cc_address_list) == 1

    assert ia1.variation_requests.count() == 0
    assert ia2.variation_requests.count() == 2

    assert ia1.case_notes.count() == 1
    assert ia2.case_notes.count() == 2

    assert ia1.update_requests.count() == 3
    assert ia2.update_requests.count() == 0

    cn1, cn2, cn3 = web.CaseNote.objects.order_by("pk")
    assert cn1.files.count() == 2
    assert cn2.files.count() == 1
    assert cn3.files.count() == 0

    assert ia1.further_information_requests.count() == 3
    assert ia2.further_information_requests.count() == 0

    fir1, fir2, fir3 = ia1.further_information_requests.order_by("pk")

    assert len(fir1.email_cc_address_list) == 2
    assert len(fir2.email_cc_address_list) == 1
    assert fir3.email_cc_address_list is None

    assert fir1.files.count() == 2
    assert fir2.files.count() == 1
    assert fir3.files.count() == 0

    assert ia1.endorsements.count() == 2
    assert ia2.endorsements.count() == 0


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

    factory.CountryFactory(id=1, name="My Test Country")
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

        dm.ImportApplicationLicence.objects.create(ima=process, status="AB", imad_id=ia.imad_id)

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

    call_command("export_from_v1", "--skip_ref", "--skip_user", "--skip_file", "--skip_export")
    call_command("extract_v1_xml", "--skip_export")

    oil1, oil2 = dm.OpenIndividualLicenceApplication.objects.filter(pk__in=pk_range).order_by("pk")

    assert oil1.section1 is True
    assert oil1.section2 is True
    assert oil2.section1 is True
    assert oil2.section2 is False

    call_command("import_v1_data", "--skip_export")

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

    factory.CountryFactory(id=1, name="My Test Country")
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

        dm.ImportApplicationLicence.objects.create(
            ima=process, status="TX TEST", imad_id=ia.imad_id
        )
        dm.TextilesApplication.objects.create(imad=ia)

    call_command("export_from_v1", "--skip_ref", "--skip_user", "--skip_file", "--skip_export")
    call_command("import_v1_data", "--skip_export")

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


export_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Exporter, web.Exporter),
        (dm.Office, web.Office),
        (dm.Process, web.Process),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.VariationRequest, web.VariationRequest),
        (dm.CaseNote, web.CaseNote),
        (dm.CaseEmail, web.CaseEmail),
        (dm.FurtherInformationRequest, web.FurtherInformationRequest),
        (dm.UpdateRequest, web.UpdateRequest),
    ],
    "import_application": [],
    "export_application": [
        (dm.ProductLegislation, web.ProductLegislation),
        (dm.ExportApplicationType, web.ExportApplicationType),
        (dm.ExportApplication, web.ExportApplication),
        (
            dm.CertificateOfGoodManufacturingPracticeApplication,
            web.CertificateOfGoodManufacturingPracticeApplication,
        ),
        (dm.CertificateOfManufactureApplication, web.CertificateOfManufactureApplication),
        (dm.GMPFile, web.GMPFile),
        (dm.GMPBrand, web.GMPBrand),
        (dm.CertificateOfFreeSaleApplication, web.CertificateOfFreeSaleApplication),
        (dm.CFSSchedule, web.CFSSchedule),
        (dm.CFSProduct, web.CFSProduct),
        (dm.CFSProductType, web.CFSProductType),
        (dm.CFSProductActiveIngredient, web.CFSProductActiveIngredient),
        (dm.ExportApplicationCertificate, web.ExportApplicationCertificate),
        (dm.ExportCaseDocument, web.CaseDocumentReference),
        (
            dm.ExportCertificateCaseDocumentReferenceData,
            web.ExportCertificateCaseDocumentReferenceData,
        ),
    ],
    "file": [
        (dm.File, web.File),
    ],
}

export_query_model = {
    "user": [],
    "file": [(q_f, "gmp_files", dm.FileCombined), (q_f, "export_case_note_docs", dm.FileCombined)],
    "import_application": [],
    "export_application": [
        (q_u, "exporters", dm.Exporter),
        (q_u, "exporter_offices", dm.Office),
        (q_ex, "product_legislation", dm.ProductLegislation),
        (q_ex, "export_application_type", dm.ExportApplicationType),
        (q_ex, "gmp_application", dm.CertificateOfGoodManufacturingPracticeApplication),
        (q_ex, "com_application", dm.CertificateOfManufactureApplication),
        (q_ex, "cfs_application", dm.CertificateOfFreeSaleApplication),
        (q_ex, "cfs_schedule", dm.CFSSchedule),
        (q_ex, "export_application_countries", dm.ExportApplicationCountries),
        (q_ex, "export_certificate", dm.ExportApplicationCertificate),
        (q_ex, "export_certificate_docs", dm.ExportCertificateCaseDocumentReferenceData),
        (q_ex, "export_variations", dm.VariationRequest),
        (q_ex, "beis_emails", dm.CaseEmail),
        (q_ex, "hse_emails", dm.CaseEmail),
    ],
    "reference": [
        (q_ref, "country_group", dm.CountryGroup),
        (q_ref, "country", dm.Country),
    ],
}

export_m2m = {
    "export_application": [
        (dm.CaseNote, web.ExportApplication, "case_notes"),
        (dm.CaseEmail, web.ExportApplication, "case_emails"),
        (dm.FurtherInformationRequest, web.ExportApplication, "further_information_requests"),
        (dm.UpdateRequest, web.ExportApplication, "update_requests"),
        (dm.CaseNoteFile, web.CaseNote, "files"),
        (dm.VariationRequest, web.ExportApplication, "variation_requests"),
        (dm.CFSLegislation, web.CFSSchedule, "legislations"),
        (dm.ExportApplicationCountries, web.ExportApplication, "countries"),
        (dm.GMPFile, web.CertificateOfGoodManufacturingPracticeApplication, "supporting_documents"),
    ],
    "import_application": [],
}

export_xml = {
    "export_application": [
        xml_parser.CFSLegislationParser,
        xml_parser.CFSProductParser,
        xml_parser.ProductTypeParser,
        xml_parser.ActiveIngredientParser,
        xml_parser.CaseNoteExportParser,
        xml_parser.FIRExportParser,
        xml_parser.UpdateExportParser,
    ],
    "import_application": [],
}


@override_settings(ALLOW_DATA_MIGRATION=True)
@override_settings(APP_ENV="production")
@override_settings(ICMS_PROD_USER="TestUser")
@override_settings(ICMS_PROD_PASSWORD="1234")
@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, export_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, export_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, export_query_model)
@mock.patch.dict(DATA_TYPE_XML, export_xml)
def test_import_export_data(mock_connect):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("extract_v1_xml")
    call_command("import_v1_data")

    assert web.CertificateOfGoodManufacturingPracticeApplication.objects.count() == 3
    ea1, ea2, ea3 = web.ExportApplication.objects.filter(
        process_ptr__process_type=web.ProcessTypes.GMP
    ).order_by("pk")
    assert ea1.countries.count() == 0
    assert ea2.countries.count() == 3
    assert ea3.countries.count() == 1

    assert ea1.variation_requests.count() == 0
    assert ea2.variation_requests.count() == 0
    assert ea3.variation_requests.count() == 1

    assert ea1.update_requests.count() == 0
    assert ea2.update_requests.count() == 1
    assert ea3.update_requests.count() == 0

    assert ea1.case_notes.count() == 0
    assert ea2.case_notes.count() == 2
    assert ea2.case_notes.filter(is_active=True).count() == 1
    assert ea3.case_notes.count() == 0

    assert ea1.case_emails.count() == 0
    assert ea2.case_emails.count() == 0
    assert ea3.case_emails.count() == 2

    assert ea1.further_information_requests.count() == 0
    assert ea2.further_information_requests.count() == 0
    assert ea3.further_information_requests.count() == 0

    case_note1 = ea2.case_notes.filter(is_active=True).first()
    assert case_note1.note == "This is a case note"
    # assert case_note1.create_datetime == datetime(2022, 9, 20, 8, 31, 34)
    assert case_note1.files.count() == 1

    assert ea1.certificates.count() == 0
    assert ea2.certificates.count() == 1
    assert ea3.certificates.count() == 2

    cert1 = ea2.certificates.first()
    cert2, cert3 = ea3.certificates.order_by("pk")

    assert cert1.status == "DR"
    assert cert2.status == "AR"
    assert cert2.document_references.count() == 0
    assert cert3.status == "AC"
    assert cert3.document_references.count() == 1

    refs = cert1.document_references.order_by("pk")
    ref2 = cert3.document_references.first()

    assert refs.count() == 3
    assert refs[0].reference == "GMP/2022/00001"
    assert refs[0].reference_data.gmp_brand_id == 2
    assert refs[0].reference_data.country_id == 1
    assert refs[1].reference == "GMP/2022/00002"
    assert refs[1].reference_data.gmp_brand_id == 2
    assert refs[1].reference_data.country_id == 2
    assert refs[2].reference == "GMP/2022/00003"
    assert refs[2].reference_data.gmp_brand_id == 2
    assert refs[2].reference_data.country_id == 3

    assert ref2.reference == "GMP/2022/00004"
    assert ref2.reference_data.gmp_brand_id == 3
    assert ref2.reference_data.country_id == 1

    gmp1, gmp2, gmp3 = web.CertificateOfGoodManufacturingPracticeApplication.objects.order_by("pk")

    assert gmp1.supporting_documents.count() == 1
    assert gmp1.supporting_documents.first().file_type == "BRC_GSOCP"
    assert gmp1.brands.count() == 0

    assert gmp2.supporting_documents.count() == 2
    assert gmp2.supporting_documents.filter(file_type="ISO_22716").count() == 1
    assert gmp2.supporting_documents.filter(file_type="ISO_17065").count() == 1
    assert gmp2.brands.count() == 1
    assert gmp2.brands.first().brand_name == "A brand"

    assert gmp3.supporting_documents.count() == 1
    assert gmp3.supporting_documents.first().file_type == "ISO_17021"
    assert gmp3.brands.count() == 1
    assert gmp3.brands.first().brand_name == "Another brand"

    assert web.CertificateOfManufactureApplication.objects.count() == 3
    com1, com2, com3 = web.CertificateOfManufactureApplication.objects.order_by("pk")

    ea4, ea5, ea6 = web.ExportApplication.objects.filter(
        process_ptr__process_type=web.ProcessTypes.COM
    ).order_by("pk")

    assert ea4.countries.count() == 0
    assert ea5.countries.count() == 1
    assert ea6.countries.count() == 1

    assert ea4.variation_requests.count() == 0
    assert ea5.variation_requests.count() == 0
    assert ea6.variation_requests.count() == 0

    assert ea4.update_requests.count() == 0
    assert ea5.update_requests.count() == 2
    assert ea6.update_requests.count() == 0

    vr2, vr3 = ea5.update_requests.order_by("pk")
    assert vr2.status == "OPEN"
    assert vr3.status == "DELETED"

    assert ea4.case_notes.count() == 0
    assert ea5.case_notes.count() == 0
    assert ea6.case_notes.count() == 0

    assert ea4.case_emails.count() == 0
    assert ea5.case_emails.count() == 0
    assert ea6.case_emails.count() == 0

    assert ea4.further_information_requests.count() == 0
    assert ea5.further_information_requests.count() == 0
    assert ea6.further_information_requests.count() == 1

    fir1 = ea6.further_information_requests.first()
    assert fir1.status == "CLOSED"
    assert len(fir1.email_cc_address_list) == 1

    assert ea4.certificates.count() == 0
    assert ea5.certificates.count() == 1
    assert ea6.certificates.count() == 1

    cert4 = ea5.certificates.first()
    cert5 = ea6.certificates.first()

    assert cert4.status == "DR"
    assert cert4.document_references.count() == 1
    assert cert5.status == "AC"
    assert cert5.document_references.count() == 1

    ref3 = cert4.document_references.first()
    ref4 = cert5.document_references.first()

    assert ref3.reference == "COM/2022/00001"
    assert ref3.reference_data.gmp_brand_id is None
    assert ref3.reference_data.country_id == 1

    assert ref4.reference == "COM/2022/00002"
    assert ref4.reference_data.gmp_brand_id is None
    assert ref4.reference_data.country_id == 1

    assert com1.is_pesticide_on_free_sale_uk is None
    assert com1.is_manufacturer is None
    assert com1.product_name is None
    assert com1.chemical_name is None
    assert com1.manufacturing_process is None

    assert com2.is_pesticide_on_free_sale_uk is True
    assert com2.is_manufacturer is False
    assert com2.product_name == "A product"
    assert com2.chemical_name == "A chemical"
    assert com2.manufacturing_process == "Test"

    assert com3.is_pesticide_on_free_sale_uk is False
    assert com3.is_manufacturer is True
    assert com3.product_name == "Another product"
    assert com3.chemical_name == "Another chemical"
    assert com3.manufacturing_process == "Test process"

    assert web.CertificateOfFreeSaleApplication.objects.count() == 3
    cfs1, cfs2, cfs3 = web.CertificateOfFreeSaleApplication.objects.order_by("pk")

    ea7, ea8, ea9 = web.ExportApplication.objects.filter(
        process_ptr__process_type=web.ProcessTypes.CFS
    ).order_by("pk")

    assert ea7.countries.count() == 0
    assert ea8.countries.count() == 1
    assert ea9.countries.count() == 1

    assert ea7.variation_requests.count() == 0
    assert ea8.variation_requests.count() == 0
    assert ea9.variation_requests.count() == 2

    assert ea7.update_requests.count() == 0
    assert ea8.update_requests.count() == 0
    assert ea9.update_requests.count() == 0

    assert ea7.case_notes.count() == 0
    assert ea8.case_notes.count() == 0
    assert ea9.case_notes.count() == 2

    assert ea7.case_emails.count() == 0
    assert ea8.case_emails.count() == 0
    assert ea9.case_emails.count() == 2

    assert ea7.further_information_requests.count() == 0
    assert ea8.further_information_requests.count() == 2
    assert ea9.further_information_requests.count() == 0

    fir2, fir3 = ea8.further_information_requests.order_by("pk")
    assert fir2.status == "OPEN"
    assert fir3.status == "DELETED"
    assert len(fir2.email_cc_address_list) == 2

    case_note2, case_note3 = ea9.case_notes.order_by("pk")
    assert case_note2.files.count() == 0
    assert case_note3.files.count() == 2

    assert ea7.certificates.count() == 0
    assert ea8.certificates.count() == 1
    assert ea9.certificates.count() == 3

    cert6 = ea8.certificates.first()
    cert7, cert8, cert9 = ea9.certificates.order_by("pk")

    assert cert6.status == "DR"
    assert cert6.document_references.count() == 1
    assert cert7.status == "AR"
    assert cert7.document_references.count() == 0
    assert cert8.status == "AR"
    assert cert8.document_references.count() == 0
    assert cert9.status == "AC"
    assert cert9.document_references.count() == 1

    ref5 = cert6.document_references.first()
    assert ref5.reference == "CFS/2022/00001"
    assert ref5.reference_data.gmp_brand_id is None
    assert ref5.reference_data.country_id == 1

    ref6 = cert9.document_references.first()
    assert ref6.reference == "CFS/2022/00002"
    assert ref6.reference_data.gmp_brand_id is None
    assert ref6.reference_data.country_id == 1

    assert cfs1.schedules.count() == 0
    assert cfs2.schedules.count() == 1
    assert cfs3.schedules.count() == 2

    sch1 = cfs2.schedules.first()
    sch2, sch3 = cfs3.schedules.order_by("pk")

    assert sch1.legislations.count() == 0
    assert sch1.is_biocidal() is False
    assert sch2.legislations.count() == 2
    assert sch2.is_biocidal() is False
    assert sch3.legislations.count() == 1
    assert sch3.is_biocidal() is True

    assert sch1.products.count() == 3
    assert sch2.products.count() == 0
    assert sch3.products.count() == 2

    for p in sch1.products.all():
        assert p.active_ingredients.count() == 0
        assert p.product_type_numbers.count() == 0

    p1, p2 = sch3.products.order_by("pk")

    assert p1.active_ingredients.count() == 2
    assert p1.product_type_numbers.count() == 2
    assert p2.active_ingredients.count() == 1
    assert p2.product_type_numbers.count() == 1
