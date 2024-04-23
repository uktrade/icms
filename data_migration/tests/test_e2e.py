import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command
from django.db.models import QuerySet

from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
from data_migration.management.commands.types import QueryModel
from data_migration.utils import xml_parser
from web import models as web

from . import utils

sil_xml_parsers = [
    xml_parser.ConstabularyEmailAttachments,
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
        (dm.Template, web.Template),
        (dm.UniqueReference, web.UniqueReference),
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
            QueryModel(queries.country, "country", dm.Country),
            QueryModel(queries.country_group, "country_group", dm.CountryGroup),
            QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
            QueryModel(
                queries.obsolete_calibre_group, "obsolete_calibre_group", dm.ObsoleteCalibreGroup
            ),
            QueryModel(queries.obsolete_calibre, "obsolete_calibre", dm.ObsoleteCalibre),
            QueryModel(queries.section5_clauses, "section5_clauses", dm.Section5Clause),
            QueryModel(queries.template, "templates", dm.Template),
        ],
        "file_folder": [
            QueryModel(queries.file_folders_folder_type, "Case Note Folders", dm.FileFolder),
            QueryModel(queries.file_targets_folder_type, "Case Note File Targets", dm.FileTarget),
            QueryModel(queries.fir_file_folders, "FIR File Folders", dm.FileFolder),
            QueryModel(queries.fir_file_targets, "FIR File Targets", dm.FileTarget),
            QueryModel(queries.import_application_folders, "Application Folders", dm.FileFolder),
            QueryModel(
                queries.import_application_file_targets, "Application File Targets", dm.FileTarget
            ),
            QueryModel(queries.fa_certificate_folders, "FA Certificate Folders", dm.FileFolder),
            QueryModel(
                queries.fa_certificate_file_targets, "FA Certificate File Targets", dm.FileTarget
            ),
        ],
        "file": [
            QueryModel(queries.file_objects_folder_type, "Case Note Files", dm.File),
            QueryModel(queries.fir_files, "FIR Files", dm.File),
            QueryModel(queries.import_application_files, "Application Files", dm.File),
            QueryModel(queries.fa_certificate_files, "FA Certificate Files", dm.File),
            QueryModel(
                queries.fa_supplementary_report_upload_files,
                "supplementary_report_uploads",
                dm.File,
            ),
            QueryModel(queries.ia_licence_docs, "ia_licence_docs", dm.CaseDocument),
        ],
        "import_application": [
            QueryModel(queries.ia_licence_doc_refs, "Licence Doc Refs", dm.UniqueReference),
            QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
            QueryModel(queries.sil_application, "sil_application", dm.SILApplication),
            QueryModel(queries.ia_licence, "ia_licence", dm.ImportApplicationLicence),
            QueryModel(
                queries.ia_document_pack_acknowledged,
                "Import Document Pack Acknowledgement",
                dm.DocumentPackAcknowledgement,
            ),
            QueryModel(queries.fa_authorities, "fa_authorities", dm.FirearmsAuthority),
            QueryModel(
                queries.fa_authority_linked_offices,
                "fa_authority_linked_offices",
                dm.FirearmsAuthorityOffice,
            ),
            QueryModel(queries.section5_authorities, "section5_authorities", dm.Section5Authority),
            QueryModel(
                queries.section5_linked_offices,
                "section5_linked_offices",
                dm.Section5AuthorityOffice,
            ),
            QueryModel(queries.sil_checklist, "sil_checklist", dm.SILChecklist),
            QueryModel(queries.constabulary_emails, "constabulary_emails", dm.CaseEmail),
            QueryModel(queries.case_note, "case_note", dm.CaseNote),
            QueryModel(queries.update_request, "update_request", dm.UpdateRequest),
            QueryModel(queries.fir, "fir", dm.FurtherInformationRequest),
            QueryModel(queries.endorsement, "endorsement", dm.EndorsementImportApplication),
        ],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.importers, "importers", dm.Importer),
            QueryModel(queries.importer_offices, "importer_offices", dm.Office),
            QueryModel(queries.exporters, "exporters", dm.Exporter),
            QueryModel(queries.exporter_offices, "exporter_offices", dm.Office),
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
            (dm.VariationRequest, web.ImportApplication, "variation_requests"),
            (dm.CaseEmail, web.ImportApplication, "case_emails"),
            (dm.ConstabularyEmailAttachments, web.CaseEmail, "attachments"),
            (dm.UpdateRequest, web.ImportApplication, "update_requests"),
            (dm.FurtherInformationRequest, web.ImportApplication, "further_information_requests"),
            (dm.FirearmsAuthorityOffice, web.FirearmsAuthority, "linked_offices"),
            (dm.Section5AuthorityOffice, web.Section5Authority, "linked_offices"),
            (dm.DocumentPackAcknowledgement, web.ImportApplicationLicence, "cleared_by"),
            (dm.DocumentPackAcknowledgement, web.ImportApplication, "cleared_by"),
        ],
        "user": [
            (dm.Office, web.Importer, "offices"),
            (dm.Office, web.Exporter, "offices"),
        ],
        "file": [
            (dm.CaseNoteFile, web.CaseNote, "files"),
            (dm.FIRFile, web.FurtherInformationRequest, "files"),
            (dm.FirearmsAuthorityFile, web.FirearmsAuthority, "files"),
            (dm.Section5AuthorityFile, web.Section5Authority, "files"),
            (dm.SILUserSection5, web.SILApplication, "user_section5"),
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
    call_command("post_migration", "--skip_perms", "--skip_add_data")

    importers = web.Importer.objects.order_by("pk")
    assert importers.count() == 3
    assert importers[0].offices.count() == 0
    assert importers[1].offices.count() == 2
    assert importers[2].offices.count() == 1

    fa_auth1: web.FirearmsAuthority
    fa_auth2: web.FirearmsAuthority
    fa_auth1, fa_auth2 = web.FirearmsAuthority.objects.filter(is_active=True).order_by("pk")
    assert fa_auth1.linked_offices.count() == 2
    assert fa_auth1.files.count() == 1
    assert fa_auth2.linked_offices.count() == 1
    assert fa_auth2.files.count() == 2

    archived_fa_auth = web.FirearmsAuthority.objects.get(is_active=False)
    assert archived_fa_auth.archive_reason == ["OTHER", "WITHDRAWN"]
    assert archived_fa_auth.other_archive_reason == "Given Reason"

    sec5_auth1: web.Section5Authority
    sec5_auth2: web.Section5Authority
    sec5_auth1, sec5_auth2 = web.Section5Authority.objects.filter(is_active=True).order_by("pk")
    assert sec5_auth1.linked_offices.count() == 2
    assert sec5_auth1.files.count() == 1
    assert sec5_auth2.linked_offices.count() == 1
    assert sec5_auth2.files.count() == 1

    archived_sec_5 = web.Section5Authority.objects.get(is_active=False)
    assert archived_sec_5.archive_reason == ["REFUSED"]
    assert archived_sec_5.other_archive_reason is None

    assert web.SILApplication.objects.count() == 3
    sil1, sil2, sil3 = web.SILApplication.objects.order_by("pk")

    assert sil1.licences.count() == 1
    assert sil2.licences.count() == 3
    assert sil2.licences.filter(status="AC").count() == 1

    assert list(sil1.cleared_by.values_list("id", flat=True)) == [2]
    assert list(sil2.cleared_by.values_list("id", flat=True).order_by("id")) == [2, 3]
    assert list(sil3.cleared_by.values_list("id", flat=True)) == []

    l1: web.ImportApplicationLicence = sil1.licences.first()
    sil2_licences: QuerySet[web.ImportApplicationLicence] = sil2.licences.order_by("id")
    l2, l3, l4 = sil2_licences

    assert l1.created_at == dt.datetime(2022, 4, 27, 10, 43, tzinfo=dt.UTC)
    assert set(l1.document_references.values_list("reference", flat=True)) == {"1234A", None}
    assert l1.document_references.filter(document_type="LICENCE").count() == 1
    assert l1.document_references.filter(document_type="COVER_LETTER").count() == 1
    assert list(l1.cleared_by.values_list("id", flat=True)) == [2]

    assert list(l2.document_references.values_list("reference", flat=True)) == ["1235B"]
    assert l2.document_references.filter(document_type="LICENCE").count() == 1
    assert l2.document_references.filter(document_type="COVER_LETTER").count() == 0
    assert list(l2.cleared_by.values_list("id", flat=True).order_by("id")) == []

    assert l3.document_references.count() == 1
    assert list(l3.cleared_by.values_list("id", flat=True)) == [2]
    assert l3.document_references.first().reference == "1236C"

    assert list(l4.document_references.values_list("reference", flat=True)) == ["1237E", None]
    assert l4.document_references.filter(document_type="LICENCE").count() == 1
    assert l4.document_references.filter(document_type="COVER_LETTER").count() == 1
    assert list(l4.cleared_by.values_list("id", flat=True)) == [3, 2]

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
    assert sil2.user_section5.count() == 0

    u_sec5_1, u_sec5_2 = sil1.user_section5.order_by("id")
    assert u_sec5_1.created_datetime == dt.datetime(2022, 4, 27, 12, 30, tzinfo=dt.UTC)
    assert u_sec5_2.created_datetime == dt.datetime(2022, 3, 23, 11, 47, tzinfo=dt.UTC)

    ia1 = sil1.importapplication_ptr
    ia2 = sil2.importapplication_ptr
    ia3 = sil3.importapplication_ptr

    assert ia1.last_updated_by_id == 2
    assert ia1.created == dt.datetime(2022, 4, 22, 9, 23, 22, tzinfo=dt.UTC)
    assert ia1.importcontact_set.count() == 0

    assert ia2.last_updated_by_id == 0
    assert ia2.importcontact_set.count() == 2
    assert ia2.created == dt.datetime(2022, 4, 22, 8, 44, 44, tzinfo=dt.UTC)
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
    assert ia1.case_emails.filter(template_code="IMA_CONSTAB_EMAIL").count() == 3
    assert ia2.case_emails.count() == 0

    open_email = ia1.case_emails.get(status="OPEN")
    assert len(open_email.cc_address_list) == 2
    assert open_email.attachments.count() == 2

    closed_email = ia1.case_emails.get(status="CLOSED")
    assert len(closed_email.cc_address_list) == 1
    assert closed_email.attachments.count() == 0

    assert ia1.reference == "IMA/2022/1234"
    assert ia1.licence_reference.prefix == "ILD"
    assert ia1.licence_reference.year is None
    assert ia1.licence_reference.reference == 1234
    assert web.UniqueReference.objects.get(prefix="IMA", year=2022, reference=1234)

    assert ia2.reference == "IMA/2022/2345/2"
    assert ia2.licence_reference.prefix == "ILD"
    assert ia2.licence_reference.year is None
    assert ia2.licence_reference.reference == 1237
    assert web.UniqueReference.objects.get(prefix="IMA", year=2022, reference=2345)

    assert ia3.reference == "IMA/2022/2346/1"
    assert ia3.licence_reference is None
    assert web.UniqueReference.objects.get(prefix="IMA", year=2022, reference=2346)

    assert ia1.variation_requests.count() == 0
    assert ia2.variation_requests.count() == 2

    vr1, vr2 = ia2.variation_requests.order_by("pk")
    assert vr1.extension_flag is False
    assert vr1.status == web.VariationRequest.Statuses.REJECTED
    assert vr1.requested_datetime == dt.datetime(2022, 4, 9, tzinfo=dt.UTC)
    assert vr1.requested_by_id == 2
    assert vr1.what_varied == "Licence extended"
    assert vr1.why_varied == "Extension"
    assert vr1.reject_cancellation_reason == "Wrong"
    assert vr1.closed_datetime == dt.datetime(2022, 4, 9, tzinfo=dt.UTC)
    assert vr1.closed_by_id == 2
    assert vr1.update_request_reason is None

    assert vr2.extension_flag is True
    assert vr2.status == web.VariationRequest.Statuses.OPEN
    assert vr2.requested_datetime == dt.datetime(2022, 4, 10, tzinfo=dt.UTC)
    assert vr2.requested_by_id == 2
    assert vr2.what_varied == "Licence extended by 4 months"
    assert vr2.why_varied == "Extension request"
    assert vr2.reject_cancellation_reason is None
    assert vr2.closed_datetime is None
    assert vr2.closed_by_id is None
    assert vr2.update_request_reason == "Open Update"

    assert ia1.case_notes.count() == 1
    assert ia2.case_notes.count() == 2

    assert ia1.update_requests.count() == 3
    assert ia2.update_requests.count() == 0

    cn1, cn2, cn3 = web.CaseNote.objects.order_by("pk")
    assert cn1.files.count() == 2
    assert cn1.create_datetime == dt.datetime(2020, 1, 1, 11, 12, 13, tzinfo=dt.UTC)
    assert cn1.created_by_id == 2
    assert cn1.updated_at == dt.datetime(2020, 1, 1, 11, 12, 13, tzinfo=dt.UTC)
    assert cn1.updated_by_id == 2
    assert cn1.is_active is True

    assert cn2.files.count() == 1
    assert cn2.is_active is True

    assert cn3.files.count() == 0
    assert cn3.is_active is True

    assert ia1.further_information_requests.count() == 3
    assert ia2.further_information_requests.count() == 0

    fir1, fir2, fir3 = ia1.further_information_requests.order_by("pk")

    assert fir1.requested_datetime == dt.datetime(2021, 1, 2, 12, 23, tzinfo=dt.UTC)

    assert fir1.files.count() == 2
    assert fir2.files.count() == 1
    assert fir3.files.count() == 0

    assert ia1.endorsements.count() == 2
    assert ia2.endorsements.count() == 0

    p1, p2 = ia1.process_ptr, ia2.process_ptr

    assert p1.created == dt.datetime(2022, 4, 22, 9, 23, 22, tzinfo=dt.UTC)
    assert p1.tasks.count() == 1
    assert p1.tasks.first().task_type == web.Task.TaskType.PROCESS

    assert p2.created == dt.datetime(2022, 4, 22, 8, 44, 44, tzinfo=dt.UTC)
    assert p2.tasks.count() == 0


oil_xml_parsers = [
    xml_parser.ImportContactParser,
    xml_parser.OILSupplementaryReportParser,
    xml_parser.OILReportFirearmParser,
    xml_parser.DFLGoodsCertificateParser,
    xml_parser.DFLSupplementaryReportParser,
    xml_parser.DFLReportFirearmParser,
    xml_parser.WithdrawalImportParser,
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
        (dm.Template, web.Template),
        (dm.UniqueReference, web.UniqueReference),
    ],
    "import_application": [
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Process, web.Process),
        (dm.ImportApplication, web.ImportApplication),
        (dm.ImportContact, web.ImportContact),
        (dm.OpenIndividualLicenceApplication, web.OpenIndividualLicenceApplication),
        (dm.DFLApplication, web.DFLApplication),
        (dm.DFLGoodsCertificate, web.DFLGoodsCertificate),
        (dm.DFLSupplementaryInfo, web.DFLSupplementaryInfo),
        (dm.DFLSupplementaryReport, web.DFLSupplementaryReport),
        (dm.DFLSupplementaryReportFirearm, web.DFLSupplementaryReportFirearm),
        (dm.ChecklistFirearmsOILApplication, web.ChecklistFirearmsOILApplication),
        (dm.OILSupplementaryInfo, web.OILSupplementaryInfo),
        (dm.OILSupplementaryReport, web.OILSupplementaryReport),
        (dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
        (dm.WithdrawApplication, web.WithdrawApplication),
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
            QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
            QueryModel(
                queries.oil_application, "oil_application", dm.OpenIndividualLicenceApplication
            ),
            QueryModel(queries.oil_checklist, "oil_checklist", dm.ChecklistFirearmsOILApplication),
            QueryModel(queries.dfl_application, "dfl_application", dm.DFLApplication),
        ],
        "reference": [
            QueryModel(queries.country, "country", dm.Country),
            QueryModel(queries.country_group, "country_group", dm.CountryGroup),
            QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
            QueryModel(queries.constabularies, "constabularies", dm.Constabulary),
            QueryModel(queries.template, "templates", dm.Template),
        ],
        "file_folder": [
            QueryModel(
                queries.import_application_folders, "Import Application Folders", dm.FileFolder
            ),
            QueryModel(
                queries.import_application_file_targets,
                "Import Application File Targets",
                dm.FileTarget,
            ),
        ],
        "file": [
            QueryModel(queries.import_application_files, "Import Application Files", dm.File),
            QueryModel(
                queries.fa_supplementary_report_upload_files,
                "supplementary_report_uploads",
                dm.File,
            ),
        ],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.importers, "importers", dm.Importer),
            QueryModel(queries.importer_offices, "importer_offices", dm.Office),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_XML, {"import_application": oil_xml_parsers, "user": []})
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, oil_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "import_application": [(dm.Office, web.Importer, "offices")],
        "export_application": [],
        "file": [],
        "user": [],
    },
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
    call_command("post_migration", "--skip_perms", "--skip_add_data")

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

    sr1 = oil1.supplementary_info.reports.first()
    sr2, sr3 = oil2.supplementary_info.reports.order_by("pk")

    assert sr1.firearms.count() == 1
    assert sr2.firearms.count() == 2
    assert sr3.firearms.count() == 1

    assert oil1.importapplication_ptr.process_ptr.tasks.count() == 0
    assert oil2.importapplication_ptr.process_ptr.tasks.count() == 0

    dfl = web.DFLApplication.objects.get(status="COMPLETED")
    assert dfl.proof_checked is True
    assert dfl.constabulary_id == 1
    assert dfl.supplementary_info.reports.count() == 1
    assert dfl.cover_letter_text == utils.xml_data.cover_letter_text_dfl_v2

    sr4 = dfl.supplementary_info.reports.first()
    assert sr4.firearms.filter(is_upload=True).count() == 1
    assert sr4.firearms.filter(is_manual=True).count() == 1

    dfl_revoked = web.DFLApplication.objects.get(status="REVOKED")
    assert dfl_revoked.licences.count() == 1
    assert dfl_revoked.licences.filter(status="RE").count() == 1

    dfl_withdrawn = web.DFLApplication.objects.get(status="WITHDRAWN")
    assert dfl_withdrawn.withdrawals.count() == 3
    (
        w1,
        w2,
        w3,
    ) = dfl_withdrawn.withdrawals.order_by("id")

    assert w1.reason == "First reason"
    assert w1.status == "DELETED"
    assert w1.is_active is False
    assert w1.response == ""
    assert w1.response_by_id is None
    assert w1.created_datetime == dt.datetime(2024, 2, 1, tzinfo=dt.UTC)
    assert w1.updated_datetime == dt.datetime(2024, 2, 1, tzinfo=dt.UTC)

    assert w2.reason == "Second reason"
    assert w2.status == "REJECTED"
    assert w2.is_active is False
    assert w2.response == "Rejection Reason"
    assert w2.response_by_id == 2
    assert w2.created_datetime == dt.datetime(2024, 2, 2, tzinfo=dt.UTC)
    assert w2.updated_datetime == dt.datetime(2024, 2, 3, tzinfo=dt.UTC)

    assert w3.reason == "Third reason"
    assert w3.status == "ACCEPTED"
    assert w3.is_active is False
    assert w3.response == ""
    assert w3.response_by_id == 2
    assert w3.created_datetime == dt.datetime(2024, 2, 2, tzinfo=dt.UTC)
    assert w3.updated_datetime == dt.datetime(2024, 2, 2, tzinfo=dt.UTC)


template_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.Importer, web.Importer),
    ],
    "reference": [
        (dm.Country, web.Country),
        (dm.CountryGroup, web.CountryGroup),
        (dm.CommodityType, web.CommodityType),
        (dm.ImportApplicationType, web.ImportApplicationType),
        (dm.Template, web.Template),
        (dm.CFSScheduleParagraph, web.CFSScheduleParagraph),
    ],
}


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "reference": [
            QueryModel(queries.country, "country", dm.Country),
            QueryModel(queries.country_group, "country_group", dm.CountryGroup),
            QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
            QueryModel(queries.ia_type, "ia type", dm.ImportApplicationType),
            QueryModel(queries.template, "template", dm.Template),
            QueryModel(queries.cfs_paragraph, "cfs paragraph", dm.CFSScheduleParagraph),
            QueryModel(queries.template_country, "template country", dm.TemplateCountry),
            QueryModel(
                queries.endorsement_template, "endorsement template", dm.EndorsementTemplate
            ),
        ],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.importers, "importers", dm.Importer),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, template_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "reference": [
            (dm.TemplateCountry, web.Template, "countries"),
            (dm.EndorsementTemplate, web.ImportApplicationType, "endorsements"),
        ],
    },
)
@mock.patch.object(oracledb, "connect")
def test_import_template(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1", "--skip_ia", "--skip_export", "--skip_file")
    call_command("import_v1_data", "--skip_ia", "--skip_export", "--skip_file")

    # Endorsement Templates

    endorsement_templates = web.Template.objects.filter(template_type="ENDORSEMENT").order_by("pk")
    assert endorsement_templates.count() == 3

    assert list(endorsement_templates.values_list("template_content", flat=True)) == [
        "First Endorsement",
        "Second Endorsement",
        "Third Endorsement",
    ]

    assert list(
        web.ImportApplicationType.objects.get(id=1).endorsements.values_list("id", flat=True)
    ) == [1]

    assert list(
        web.ImportApplicationType.objects.get(id=5).endorsements.values_list("id", flat=True)
    ) == [2, 3]

    assert list(
        web.ImportApplicationType.objects.get(id=6).endorsements.values_list("id", flat=True)
    ) == [1, 2, 3]

    # Letter Templates

    assert web.Template.objects.filter(template_type="LETTER_TEMPLATE").count() == 1
    letter_template = web.Template.objects.get(template_type="LETTER_TEMPLATE")
    assert letter_template.template_content == utils.xml_data.letter_template_cleaned

    # Email Templates
    assert web.Template.objects.filter(template_type="EMAIL_TEMPLATE").count() == 1
    email_template = web.Template.objects.get(template_type="EMAIL_TEMPLATE")
    assert email_template.template_content == utils.xml_data.email_template

    # CFS Templates
    assert web.Template.objects.filter(template_type="CFS_SCHEDULE").count() == 1
    cfs_template = web.Template.objects.get(template_type="CFS_SCHEDULE")
    assert cfs_template.template_content is None
    assert cfs_template.paragraphs.count() == 3

    # CFS Template Paragraphs
    p1, p2, p3 = cfs_template.paragraphs.order_by("order")
    assert p1.content == "Content 1"
    assert p2.content == "Content 2"
    assert p3.content == "Content '3'"

    assert web.Template.objects.filter(template_type="CFS_DECLARATION_TRANSLATION").count() == 1
    cfs_dec_template = web.Template.objects.get(template_type="CFS_DECLARATION_TRANSLATION")
    assert cfs_dec_template.template_content == "Some translated text with ' data '"
    assert list(cfs_dec_template.countries.values_list("id", flat=True)) == [2, 3]
