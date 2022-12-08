from unittest import mock

import oracledb
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
from data_migration.queries import reference as q_ref
from data_migration.queries import user as q_u
from data_migration.utils import xml_parser
from web import models as web

from . import utils

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


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "reference": [
            (q_ref, "country", dm.Country),
            (q_ref, "country_group", dm.CountryGroup),
            (q_ref, "commodity_type", dm.CommodityType),
            (q_ref, "obsolete_calibre_group", dm.ObsoleteCalibreGroup),
            (q_ref, "obsolete_calibre", dm.ObsoleteCalibre),
            (q_ia, "section5_clauses", dm.Section5Clause),
        ],
        "file": [
            (q_f, "case_note_files", dm.FileCombined),
            (q_f, "fir_files", dm.FileCombined),
            (q_f, "sil_application_files", dm.FileCombined),
            (q_f, "fa_certificate_files", dm.FileCombined),
        ],
        "import_application": [
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
        "user": [
            (q_u, "users", dm.User),
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
            (q_u, "exporters", dm.Exporter),
            (q_u, "exporter_offices", dm.Office),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": sil_xml_parsers, "user": []})
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
            (dm.FirearmsAuthorityOffice, web.FirearmsAuthority, "linked_offices"),
            (dm.FirearmsAuthorityFile, web.FirearmsAuthority, "files"),
            (dm.Section5AuthorityOffice, web.Section5Authority, "linked_offices"),
            (dm.Section5AuthorityFile, web.Section5Authority, "files"),
            (dm.SILUserSection5, web.SILApplication, "user_section5"),
        ],
        "user": [
            (dm.Office, web.Importer, "offices"),
            (dm.Office, web.Exporter, "offices"),
        ],
    },
)
@mock.patch.object(oracledb, "connect")
def test_import_sil_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_export")
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

    assert ia1.process_ptr.tasks.count() == 1
    assert ia1.process_ptr.tasks.first().task_type == web.Task.TaskType.PROCESS
    assert ia2.process_ptr.tasks.count() == 0


oil_xml_parsers = [
    xml_parser.ImportContactParser,
    xml_parser.OILSupplementaryReportParser,
    xml_parser.OILReportFirearmParser,
]

oil_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Office, web.Office),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.CommodityType, web.CommodityType),
        (dm.Constabulary, web.Constabulary),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.OpenIndividualLicenceApplication, web.OpenIndividualLicenceApplication),
        (dm.DFLApplication, web.DFLApplication),
        (dm.ChecklistFirearmsOILApplication, web.ChecklistFirearmsOILApplication),
        (dm.OILSupplementaryInfo, web.OILSupplementaryInfo),
        (dm.OILSupplementaryReport, web.OILSupplementaryReport),
        (dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
    ],
    "file": [
        (dm.File, web.File),
    ],
}


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "import_application": [
            (q_ia, "ia_type", dm.ImportApplicationType),
            (q_ia, "oil_application", dm.OpenIndividualLicenceApplication),
            (q_ia, "oil_checklist", dm.ChecklistFirearmsOILApplication),
            (q_ia, "dfl_application", dm.DFLApplication),
        ],
        "reference": [
            (q_ref, "country", dm.Country),
            (q_ref, "country_group", dm.CountryGroup),
            (q_ref, "commodity_type", dm.CommodityType),
            (q_ref, "constabularies", dm.Constabulary),
        ],
        "file": [
            (q_f, "oil_application_files", dm.FileCombined),
            (q_f, "dfl_application_files", dm.FileCombined),
        ],
        "user": [
            (q_u, "users", dm.User),
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": oil_xml_parsers, "user": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, oil_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M, {"import_application": [(dm.Office, web.Importer, "offices")], "user": []}
)
@mock.patch.object(oracledb, "connect")
def test_import_oil_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_export")
    call_command("extract_v1_xml", "--skip_export")

    oil1, oil2 = dm.OpenIndividualLicenceApplication.objects.order_by("pk")

    assert oil1.section1 is True
    assert oil1.section2 is True
    assert oil2.section1 is True
    assert oil2.section2 is False

    call_command("import_v1_data", "--skip_export")

    oil1, oil2 = web.OpenIndividualLicenceApplication.objects.order_by("pk")

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

    assert oil1.importapplication_ptr.process_ptr.tasks.count() == 0
    assert oil2.importapplication_ptr.process_ptr.tasks.count() == 0

    dfl = web.DFLApplication.objects.first()
    assert dfl.proof_checked is True
    assert dfl.constabulary_id == 1


user_xml_parsers = {
    "import_application": [],
    "export_application": [],
    "user": [
        xml_parser.ApprovalRequestParser,
        xml_parser.AccessFIRParser,
    ],
}

user_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
        (dm.Exporter, web.Exporter),
        (dm.Office, web.Office),
        (dm.Process, web.Process),
        (dm.AccessRequest, web.AccessRequest),
        (dm.ImporterAccessRequest, web.ImporterAccessRequest),
        (dm.ExporterAccessRequest, web.ExporterAccessRequest),
        (dm.FurtherInformationRequest, web.FurtherInformationRequest),
        (dm.ApprovalRequest, web.ApprovalRequest),
        (dm.ImporterApprovalRequest, web.ImporterApprovalRequest),
        (dm.ExporterApprovalRequest, web.ExporterApprovalRequest),
    ],
    "reference": [],
    "import_application": [],
    "export_application": [],
    "file": [],
}


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "import_application": [],
        "export_application": [],
        "reference": [],
        "file": [],
        "user": [
            (q_u, "users", dm.User),
            (q_u, "importers", dm.Importer),
            (q_u, "importer_offices", dm.Office),
            (q_u, "exporters", dm.Exporter),
            (q_u, "exporter_offices", dm.Office),
            (q_u, "access_requests", dm.AccessRequest),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, user_xml_parsers)
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, user_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [],
        "export_application": [],
        "user": [
            (dm.Office, web.Importer, "offices"),
            (dm.Office, web.Exporter, "offices"),
            (dm.FurtherInformationRequest, web.AccessRequest, "further_information_requests"),
        ],
    },
)
@mock.patch.object(oracledb, "connect")
@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "web.auth.fox_hasher.FOXPBKDF2SHA1Hasher",
    ]
)
def test_import_user(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("extract_v1_xml")
    call_command("import_v1_data")

    u1, u2 = web.User.objects.filter(pk__in=[2, 3]).order_by("pk")
    assert u1.username == "test_user"
    assert u1.first_name == "Test"
    assert u1.last_name == "User"
    assert u1.email == "test.user"
    assert u1.check_password("password") is True
    assert u1.title == "Mr"
    assert u1.organisation == "Org"
    assert u1.department == "Dept"
    assert u1.job_title == "IT"
    assert u1.account_status == "ACTIVE"
    assert u1.account_status_by_id == 3

    assert u2.check_password("password123") is True
    assert u2.account_status_by_id == 3

    ar1, ar2, ar3, ar4 = web.AccessRequest.objects.order_by("pk")

    assert ar1.process_ptr.process_type == "ImporterAccessRequest"
    assert ar1.process_ptr.tasks.count() == 1
    assert ar1.reference == "IAR/0001"
    assert ar1.status == "SUBMITTED"
    assert ar1.organisation_name == "Test Org"
    assert ar1.organisation_address == "Test Address"
    assert ar1.agent_name is None
    assert ar1.agent_address == ""
    assert ar1.response is None
    assert ar1.response_reason == ""
    assert ar1.importeraccessrequest.request_type == "MAIN_IMPORTER_ACCESS"
    assert ar1.importeraccessrequest.link_id == 2
    assert ar1.further_information_requests.count() == 0
    assert ar1.approval_requests.count() == 0

    assert ar2.process_ptr.process_type == "ImporterAccessRequest"
    assert ar2.process_ptr.tasks.count() == 0
    assert ar2.reference == "IAR/0002"
    assert ar2.status == "CLOSED"
    assert ar2.agent_name == "Test Name"
    assert ar2.agent_address == "Test Address"
    assert ar2.request_reason == "Test Reason"
    assert ar2.response == "APPROVED"
    assert ar2.response_reason == "Test Reason"
    assert ar2.importeraccessrequest.request_type == "AGENT_IMPORTER_ACCESS"
    assert ar2.importeraccessrequest.link_id == 3
    assert ar2.further_information_requests.count() == 0
    assert ar2.approval_requests.count() == 1

    ar2_ar = ar2.approval_requests.first()
    assert ar2_ar.process_ptr.process_type == "ImporterApprovalRequest"
    assert ar2_ar.status == "COMPLETED"
    assert ar2_ar.response == "APPROVE"
    assert ar2_ar.response_reason == "Test Reason"
    assert ar2_ar.importerapprovalrequest.pk == ar2_ar.pk

    assert ar3.process_ptr.process_type == "ExporterAccessRequest"
    assert ar3.process_ptr.tasks.count() == 0
    assert ar3.reference == "EAR/0003"
    assert ar3.exporteraccessrequest.request_type == "MAIN_EXPORTER_ACCESS"
    assert ar3.exporteraccessrequest.link_id == 2
    assert ar3.further_information_requests.count() == 2
    assert ar3.approval_requests.count() == 0

    assert ar4.process_ptr.process_type == "ExporterAccessRequest"
    assert ar4.process_ptr.tasks.count() == 0
    assert ar4.reference == "EAR/0004"
    assert ar4.exporteraccessrequest.request_type == "AGENT_EXPORTER_ACCESS"
    assert ar4.exporteraccessrequest.link_id == 3
    assert ar4.further_information_requests.count() == 0
    assert ar4.approval_requests.count() == 1

    ar4_ar = ar4.approval_requests.first()
    assert ar4_ar.process_ptr.process_type == "ExporterApprovalRequest"
    assert ar4_ar.status == "COMPLETED"
    assert ar4_ar.response == "APPROVE"
    assert ar4_ar.response_reason == "Test Reason"
    assert ar4_ar.exporterapprovalrequest.pk == ar4_ar.pk
