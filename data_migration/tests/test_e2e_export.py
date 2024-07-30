import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command

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
from web.flow.models import ProcessTypes

from . import utils

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
        (dm.UniqueReference, web.UniqueReference),
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
        (dm.WithdrawApplication, web.WithdrawApplication),
        (dm.CertificateApplicationTemplate, web.CertificateApplicationTemplate),
        (dm.CertificateOfFreeSaleApplicationTemplate, web.CertificateOfFreeSaleApplicationTemplate),
        (dm.CFSScheduleTemplate, web.CFSScheduleTemplate),
        (dm.CFSProductTemplate, web.CFSProductTemplate),
        (dm.CFSProductActiveIngredientTemplate, web.CFSProductActiveIngredientTemplate),
        (dm.CFSProductTypeTemplate, web.CFSProductTypeTemplate),
        (
            dm.CertificateOfManufactureApplicationTemplate,
            web.CertificateOfManufactureApplicationTemplate,
        ),
    ],
    "file": [
        (dm.File, web.File),
    ],
}

export_query_model = {
    "user": [QueryModel(queries.users, "users", dm.User)],
    "file_folder": [
        QueryModel(queries.file_folders_folder_type, "GMP File Folders", dm.FileFolder),
        QueryModel(queries.file_targets_folder_type, "GMP File Targets", dm.FileTarget),
        QueryModel(queries.export_case_note_folders, "Export Case Note Doc Folders", dm.DocFolder),
    ],
    "file": [
        QueryModel(queries.file_objects_folder_type, "GMP Files", dm.File),
        QueryModel(queries.export_case_note_docs, "Export Case Note Documents", dm.File),
    ],
    "import_application": [],
    "export_application": [
        QueryModel(queries.exporters, "exporters", dm.Exporter),
        QueryModel(queries.exporter_offices, "exporter_offices", dm.Office),
        QueryModel(queries.product_legislation, "product_legislation", dm.ProductLegislation),
        QueryModel(
            queries.export_application_type, "export_application_type", dm.ExportApplicationType
        ),
        QueryModel(
            queries.gmp_application,
            "gmp_application",
            dm.CertificateOfGoodManufacturingPracticeApplication,
        ),
        QueryModel(
            queries.com_application, "com_application", dm.CertificateOfManufactureApplication
        ),
        QueryModel(queries.cfs_application, "cfs_application", dm.CertificateOfFreeSaleApplication),
        QueryModel(queries.cfs_schedule, "cfs_schedule", dm.CFSSchedule),
        QueryModel(
            queries.export_application_countries,
            "export_application_countries",
            dm.ExportApplicationCountries,
        ),
        QueryModel(
            queries.export_certificate, "export_certificate", dm.ExportApplicationCertificate
        ),
        QueryModel(
            queries.export_document_pack_acknowledged,
            "Export Document Pack Acknowledgement",
            dm.DocumentPackAcknowledgement,
        ),
        QueryModel(
            queries.export_certificate_docs,
            "export_certificate_docs",
            dm.ExportCertificateCaseDocumentReferenceData,
        ),
        QueryModel(queries.beis_emails, "beis_emails", dm.CaseEmail),
        QueryModel(queries.hse_emails, "hse_emails", dm.CaseEmail),
        QueryModel(
            queries.export_application_template,
            "Certificate Application Templates",
            dm.CertificateApplicationTemplate,
        ),
        QueryModel(
            queries.cfs_application_template,
            "CFS Application Templates",
            dm.CertificateOfFreeSaleApplicationTemplate,
        ),
        QueryModel(
            queries.com_application_template,
            "COM Application Templates",
            dm.CertificateOfManufactureApplicationTemplate,
        ),
    ],
    "reference": [
        QueryModel(queries.country_group, "country_group", dm.CountryGroup),
        QueryModel(queries.country, "country", dm.Country),
    ],
}

export_m2m = {
    "export_application": [
        (dm.CaseNote, web.ExportApplication, "case_notes"),
        (dm.CaseEmail, web.ExportApplication, "case_emails"),
        (dm.FurtherInformationRequest, web.ExportApplication, "further_information_requests"),
        (dm.UpdateRequest, web.ExportApplication, "update_requests"),
        (dm.VariationRequest, web.ExportApplication, "variation_requests"),
        (dm.CFSLegislation, web.CFSSchedule, "legislations"),
        (dm.ExportApplicationCountries, web.ExportApplication, "countries"),
        (dm.DocumentPackAcknowledgement, web.ExportApplicationCertificate, "cleared_by"),
        (dm.DocumentPackAcknowledgement, web.ExportApplication, "cleared_by"),
        (dm.CFSTemplateCountries, web.CertificateOfFreeSaleApplicationTemplate, "countries"),
        (dm.CFSTemplateLegislation, web.CFSScheduleTemplate, "legislations"),
        (dm.COMTemplateCountries, web.CertificateOfManufactureApplicationTemplate, "countries"),
    ],
    "import_application": [],
    "file": [
        (dm.CaseNoteFile, web.CaseNote, "files"),
        (dm.GMPFile, web.CertificateOfGoodManufacturingPracticeApplication, "supporting_documents"),
    ],
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
        xml_parser.VariationExportParser,
        xml_parser.WithdrawalExportParser,
        xml_parser.CFSApplicationTemplateCountryParser,
        xml_parser.COMApplicationTemplateCountryParser,
        xml_parser.CFSScheduleTemplateParser,
        xml_parser.CFSTemplateLegislationParser,
        xml_parser.CFSTemplateProductParser,
        xml_parser.CFSTemplateActiveIngredientParser,
        xml_parser.CFSTemplateProductTypeParser,
    ],
    "import_application": [],
}


@pytest.mark.django_db
@mock.patch.object(oracledb, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, export_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, export_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, export_query_model)
@mock.patch.dict(DATA_TYPE_XML, export_xml)
def test_import_export_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("extract_v1_xml")
    call_command("import_v1_data")
    call_command("post_migration", "--skip_perms", "--skip_add_data")

    assert web.CertificateOfGoodManufacturingPracticeApplication.objects.count() == 5
    assert dm.CertificateOfGoodManufacturingPracticeApplication.objects.count() == 5

    gmp1, gmp2, gmp3, gmp4, gmp5 = (
        web.CertificateOfGoodManufacturingPracticeApplication.objects.order_by("pk")
    )
    ea1: web.ExportApplication = gmp1.exportapplication
    ea2: web.ExportApplication = gmp2.exportapplication
    ea3: web.ExportApplication = gmp3.exportapplication
    ea4: web.ExportApplication = gmp4.exportapplication

    assert ea1.reference == "GA/2022/9901"
    assert web.UniqueReference.objects.get(prefix="GA", year=2022, reference=9901)

    assert ea2.reference == "GA/2022/9902"
    assert web.UniqueReference.objects.get(prefix="GA", year=2022, reference=9902)

    assert ea3.reference == "GA/2022/9903/1"
    assert web.UniqueReference.objects.get(prefix="GA", year=2022, reference=9903)

    assert ea4.reference == "GA/2022/9910"
    assert web.UniqueReference.objects.get(prefix="GA", year=2022, reference=9910)

    assert ea1.countries.count() == 0
    assert ea2.countries.count() == 3
    assert ea3.countries.count() == 1
    assert ea4.countries.count() == 0

    assert ea1.variation_requests.count() == 0
    assert ea2.variation_requests.count() == 0
    assert ea3.variation_requests.count() == 1
    assert ea4.variation_requests.count() == 0

    vr1: web.VariationRequest = ea3.variation_requests.first()
    assert vr1.what_varied == "Changes 1"
    assert vr1.requested_datetime == dt.datetime(2022, 10, 13, 11, 1, 5, tzinfo=dt.UTC)
    assert vr1.closed_datetime == dt.datetime(2022, 10, 14, 12, 1, 5, tzinfo=dt.UTC)

    assert ea1.update_requests.count() == 0
    assert ea2.update_requests.count() == 1
    assert ea3.update_requests.count() == 0
    assert ea4.update_requests.count() == 0

    upr1: web.UpdateRequest = ea2.update_requests.first()
    assert upr1.response_detail == "update request response info"
    assert upr1.response_datetime == dt.datetime(2022, 9, 21, 8, 31, 34, tzinfo=dt.UTC)
    assert upr1.response_by_id == 2

    assert ea1.case_notes.count() == 0
    assert ea2.case_notes.count() == 2
    assert ea2.case_notes.filter(is_active=True).count() == 1
    assert ea2.case_notes.filter(is_active=False).count() == 1
    assert ea3.case_notes.count() == 0
    assert ea4.case_notes.count() == 0

    assert ea1.case_emails.count() == 0
    assert ea2.case_emails.count() == 0
    assert ea3.case_emails.count() == 2
    assert ea4.case_emails.count() == 0

    assert ea1.further_information_requests.count() == 0
    assert ea2.further_information_requests.count() == 0
    assert ea3.further_information_requests.count() == 0
    assert ea4.further_information_requests.count() == 0

    case_note1 = ea2.case_notes.filter(is_active=True).first()
    assert case_note1.note == "This is a case note"
    assert case_note1.create_datetime == dt.datetime(2022, 9, 20, 8, 31, 34, tzinfo=dt.UTC)
    assert case_note1.created_by_id == 2
    assert case_note1.updated_at == dt.datetime(2022, 9, 20, 8, 31, 34, tzinfo=dt.UTC)
    assert case_note1.updated_by_id == 2
    assert case_note1.files.count() == 1

    case_note4 = ea2.case_notes.filter(is_active=False).first()
    assert case_note4.note == "This is a deleted case note"

    assert ea1.certificates.count() == 0
    assert ea2.certificates.count() == 1
    assert ea3.certificates.count() == 3
    assert ea4.certificates.count() == 1

    assert list(ea1.cleared_by.values_list("id", flat=True)) == []
    assert list(ea2.cleared_by.values_list("id", flat=True)) == []
    assert list(ea3.cleared_by.values_list("id", flat=True)) == []
    assert list(ea4.cleared_by.values_list("id", flat=True)) == []

    cert1 = ea2.certificates.first()
    cert2, cert3, cert4 = ea3.certificates.order_by("pk")

    assert list(cert1.cleared_by.values_list("id", flat=True)) == []
    assert list(cert2.cleared_by.values_list("id", flat=True)) == []
    assert list(cert3.cleared_by.values_list("id", flat=True)) == []

    assert cert1.status == "DR"
    assert cert1.case_reference == "GA/2022/9902"
    assert cert1.revoke_reason is None
    assert cert1.revoke_email_sent is False
    assert cert1.case_completion_datetime is None
    assert cert1.updated_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert1.created_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert1.document_references.count() == 3

    cert1_ref1, cert1_ref2, cert1_ref3 = cert1.document_references.order_by("pk")
    assert cert1_ref1.reference == "GMP/2022/00001"
    assert cert1_ref1.reference_data.country_id == 1
    assert cert1_ref1.check_code == "12345678"
    assert cert1_ref1.document_type == "CERTIFICATE"
    assert cert1_ref1.document.filename == "gmp-cert-1.pdf"
    assert web.UniqueReference.objects.get(prefix="GMP", year=2022, reference=1)

    assert cert1_ref2.reference == "GMP/2022/00002"
    assert cert1_ref2.reference_data.country_id == 2
    assert cert1_ref2.check_code == "56781234"
    assert web.UniqueReference.objects.get(prefix="GMP", year=2022, reference=2)

    assert cert1_ref3.reference == "GMP/2022/00003"
    assert cert1_ref3.reference_data.country_id == 3
    assert cert1_ref3.check_code == "43215678"
    assert cert1_ref3.document_type == "CERTIFICATE"
    assert cert1_ref3.document.filename == "gmp-cert-3.pdf"
    assert web.UniqueReference.objects.get(prefix="GMP", year=2022, reference=3)

    assert cert2.status == "AR"
    assert cert2.case_reference == "GA/2022/9903"
    assert cert2.revoke_reason is None
    assert cert2.revoke_email_sent is False
    assert cert2.case_completion_datetime == dt.datetime(2022, 4, 29, 0, 0, tzinfo=dt.UTC)
    assert cert2.updated_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert2.created_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert2.document_references.count() == 0

    assert cert3.status == "AC"
    assert cert3.case_reference == "CA/2022/9903/1"
    assert cert3.revoke_reason is None
    assert cert3.revoke_email_sent is False
    assert cert3.case_completion_datetime == dt.datetime(2022, 4, 29, 0, 0, tzinfo=dt.UTC)
    assert cert3.updated_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert3.created_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert3.document_references.count() == 1

    cert3_ref1 = cert3.document_references.first()
    assert cert3_ref1.reference == "GMP/2022/00004"
    assert cert3_ref1.reference_data.country_id == 1
    assert cert3_ref1.check_code == "87654321"
    assert cert3_ref1.document_type == "CERTIFICATE"
    assert cert3_ref1.document.filename == "gmp-cert-4.pdf"
    assert web.UniqueReference.objects.get(prefix="GMP", year=2022, reference=4)

    assert cert4.status == "RE"
    assert cert4.case_reference == "GA/2022/9909"
    assert cert4.revoke_reason == "No longer trading"
    assert cert4.revoke_email_sent is True
    assert cert4.case_completion_datetime == dt.datetime(2022, 4, 29, 0, 0, tzinfo=dt.UTC)
    assert cert4.updated_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert4.created_at == dt.datetime(2022, 4, 29, 13, 21, tzinfo=dt.UTC)
    assert cert4.document_references.count() == 1

    cert4_ref1 = cert4.document_references.first()
    assert cert4_ref1.reference == "GMP/2022/00005"
    assert cert4_ref1.reference_data.country_id == 1
    assert cert4_ref1.check_code == "87654355"
    assert cert4_ref1.document_type == "CERTIFICATE"
    assert cert4_ref1.document.filename == "gmp-cert-5.pdf"
    assert web.UniqueReference.objects.get(prefix="GMP", year=2022, reference=4)

    assert gmp1.reference == "GA/2022/9901"
    assert gmp1.status == "IN PROGRESS"
    assert gmp1.is_active is True
    assert gmp1.responsible_person_address_entry_type == "SEARCH"
    assert gmp1.manufacturer_address_entry_type == "SEARCH"
    assert gmp1.exporter_id == 2
    assert gmp1.created_by_id == 2
    assert gmp1.created == dt.datetime(2022, 4, 27, 0, 0, tzinfo=dt.timezone.utc)

    none_fields = [
        "finished",
        "reassign_datetime",
        "refuse_reason",
        "contact_id",
        "agent_id",
        "agent_office_id",
        "case_owner_id",
    ]
    for field in none_fields + [
        "brand_name",
        "submit_datetime",
        "last_submit_datetime",
        "gmp_certificate_issued",
        "is_responsible_person",
        "responsible_person_name",
        "responsible_person_postcode",
        "responsible_person_address",
        "responsible_person_country",
        "auditor_accredited",
        "auditor_certified",
        "submitted_by_id",
        "decision",
        "is_manufacturer",
        "manufacturer_name",
        "manufacturer_postcode",
        "manufacturer_address",
        "manufacturer_country",
    ]:
        assert getattr(gmp1, field) is None

    assert gmp1.variation_requests.count() == 0
    assert gmp1.supporting_documents.count() == 1
    gmp1_doc = gmp1.supporting_documents.first()
    assert gmp1_doc.file_type == "BRC_GSOCP"
    assert gmp1_doc.filename == "BRCGS.pdf"
    assert gmp1_doc.content_type == "pdf"

    for field in none_fields:
        assert getattr(gmp2, field) is None

    assert gmp2.reference == "GA/2022/9902"
    assert gmp2.is_active is True
    assert gmp2.is_responsible_person == "no"
    assert gmp2.is_manufacturer == "no"
    assert gmp2.status == "PROCESSING"
    assert gmp2.responsible_person_address_entry_type == "SEARCH"
    assert gmp2.manufacturer_address_entry_type == "MANUAL"
    assert gmp2.exporter_id == 3
    assert gmp2.created_by_id == 2
    assert gmp2.brand_name == "A brand"
    assert gmp2.auditor_accredited == "no"
    assert gmp2.auditor_certified is None
    assert (
        gmp2.gmp_certificate_issued
        == web.CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.BRC_GSOCP
    )
    assert gmp2.submit_datetime == dt.datetime(2022, 4, 29, 0, 0, tzinfo=dt.timezone.utc)
    assert gmp2.last_submit_datetime is not None

    assert gmp2.variation_requests.count() == 0
    assert gmp2.supporting_documents.count() == 2
    gmp2_iso_17065_file = gmp2.supporting_documents.filter(file_type="ISO_17065").first()
    assert gmp2_iso_17065_file is not None
    assert gmp2_iso_17065_file.file_type == "ISO_17065"
    assert gmp2_iso_17065_file.filename == "ISO17065.pdf"
    assert gmp2_iso_17065_file.content_type == "pdf"
    gmp2_iso_17021_file = gmp2.supporting_documents.filter(file_type="ISO_22716").first()
    assert gmp2_iso_17021_file is not None
    assert gmp2_iso_17021_file.file_type == "ISO_22716"
    assert gmp2_iso_17021_file.filename == "ISO22716.pdf"
    assert gmp2_iso_17021_file.content_type == "pdf"

    assert gmp3.reference == "GA/2022/9903/1"
    assert gmp3.is_active is True
    assert gmp3.status == "COMPLETED"
    assert gmp3.brand_name == "Another brand"
    assert gmp3.is_responsible_person == "yes"
    assert gmp3.responsible_person_name == "G. M. Potter"
    assert gmp3.responsible_person_address == "The Bridge\nLondon"
    assert gmp3.responsible_person_country == "GB"
    assert gmp3.responsible_person_postcode == "12345"
    assert gmp3.is_manufacturer == "yes"
    assert gmp3.manufacturer_name == "Cars"
    assert gmp3.manufacturer_address == "The Street\nLondon"
    assert gmp3.manufacturer_country == "GB"
    assert gmp3.manufacturer_postcode == "12345"
    assert gmp3.auditor_accredited == "yes"
    assert gmp3.auditor_certified == "yes"
    assert gmp3.submitted_by_id == 2
    assert gmp3.decision == "APPROVE"

    assert (
        gmp3.gmp_certificate_issued
        == web.CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.ISO_22716
    )
    for field in none_fields:
        assert getattr(gmp3, field) is None

    assert gmp3.variation_requests.count() == 1
    assert gmp3.supporting_documents.count() == 1

    assert gmp3.responsible_person_address_entry_type == "MANUAL"
    assert gmp3.manufacturer_address_entry_type == "MANUAL"
    gmp3_iso_17021_file = gmp3.supporting_documents.filter(file_type="ISO_17021").first()
    assert gmp3_iso_17021_file is not None
    assert gmp3_iso_17021_file.file_type == "ISO_17021"
    assert gmp3_iso_17021_file.filename == "ISO17021.pdf"
    assert gmp3_iso_17021_file.content_type == "pdf"

    assert gmp4.reference == "GA/2022/9910"
    assert gmp4.is_active is True
    assert gmp4.status == "WITHDRAWN"
    assert gmp4.brand_name == "Test brand"
    assert gmp4.decision == "REFUSE"

    assert (
        gmp4.gmp_certificate_issued
        == web.CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.ISO_22716
    )

    # In V1 when a GMP application application is a copy of another GMP application, they share the same files

    gmp5_iso_17021_file = gmp5.supporting_documents.filter(file_type="ISO_17021").first()
    assert gmp5_iso_17021_file == gmp3_iso_17021_file
    assert gmp5_iso_17021_file is not None
    assert gmp5_iso_17021_file.file_type == "ISO_17021"
    assert gmp5_iso_17021_file.filename == "ISO17021.pdf"
    assert gmp5_iso_17021_file.content_type == "pdf"

    for field in none_fields:
        assert getattr(gmp4, field) is None

    assert web.CertificateOfManufactureApplication.objects.count() == 3
    com1, com2, com3 = web.CertificateOfManufactureApplication.objects.order_by("pk")

    assert (
        web.ExportApplication.objects.filter(process_ptr__process_type=ProcessTypes.COM).count()
        == 3
    )
    ea4 = com1.exportapplication
    ea5 = com2.exportapplication
    ea6 = com3.exportapplication

    assert ea4.reference == "CA/2022/9904"
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9904)

    assert ea5.reference == "CA/2022/9905"
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9905)

    assert ea6.reference == "CA/2022/9906"
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9906)

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
    assert fir1.response_detail == "Further Information Request Data"
    assert fir1.response_datetime == dt.datetime(2022, 9, 21, 8, 31, 34, tzinfo=dt.UTC)
    assert fir1.response_by_id == 2

    assert ea4.certificates.count() == 0
    assert ea5.certificates.count() == 1
    assert ea6.certificates.count() == 1

    assert list(ea4.cleared_by.values_list("id", flat=True)) == []
    assert list(ea5.cleared_by.values_list("id", flat=True)) == []
    assert list(ea6.cleared_by.values_list("id", flat=True)) == [2]

    cert4 = ea5.certificates.first()
    cert5 = ea6.certificates.first()

    assert list(cert4.cleared_by.values_list("id", flat=True)) == []
    assert list(cert5.cleared_by.values_list("id", flat=True)) == [2]

    assert cert4.status == "DR"
    assert cert4.document_references.count() == 1
    assert cert4.case_completion_datetime is None
    assert cert4.case_reference == "CA/2022/9905"
    assert cert4.document_references.count() == 1

    assert cert5.status == "AC"
    assert cert5.document_references.count() == 1
    assert cert5.case_completion_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert cert5.case_reference == "CA/2022/9906"
    assert cert5.document_references.count() == 1

    ref3 = cert4.document_references.first()
    ref4 = cert5.document_references.first()

    assert ref3.reference == "COM/2022/00001"
    assert ref3.reference_data.country_id == 1
    assert ref3.check_code == "87651432"
    assert ref3.document_type == "CERTIFICATE"
    assert web.UniqueReference.objects.get(prefix="COM", year=2022, reference=1)

    assert ref4.reference == "COM/2022/00002"
    assert ref4.reference_data.country_id == 1
    assert ref4.check_code == "87651432"
    assert ref4.document_type == "CERTIFICATE"
    assert web.UniqueReference.objects.get(prefix="COM", year=2022, reference=2)

    assert com1.is_active is True
    assert com1.finished is None
    assert com1.is_pesticide_on_free_sale_uk is None
    assert com1.is_manufacturer is None
    assert com1.product_name is None
    assert com1.chemical_name is None
    assert com1.manufacturing_process is None

    assert com1.exporter_id == 2
    assert com1.application_type_id == 2
    assert com1.created_by_id == 2
    assert com1.last_updated_by_id == 2
    assert com1.submitted_by_id is None

    assert com1.created == dt.datetime(2022, 4, 27, 0, 0, 0, tzinfo=dt.UTC)
    assert com1.submit_datetime is None
    assert com1.last_submit_datetime is None

    assert com1.order_datetime == dt.datetime(2022, 4, 27, 0, 0, 0, tzinfo=dt.UTC)
    assert com1.last_update_datetime == dt.datetime(2022, 4, 27, 0, 0, 0, tzinfo=dt.UTC)

    assert com1.status == "IN PROGRESS"
    assert com1.reference == "CA/2022/9904"

    assert com2.is_active is True
    assert com2.finished is None
    assert com2.is_pesticide_on_free_sale_uk is True
    assert com2.is_manufacturer is False
    assert com2.product_name == "A product"
    assert com2.chemical_name == "A chemical"
    assert com2.manufacturing_process == "Test"

    assert com2.exporter_id == 3
    assert com2.application_type_id == 2
    assert com2.created_by_id == 2
    assert com2.last_updated_by_id == 2
    assert com2.submitted_by_id is None

    assert com2.created == dt.datetime(2022, 4, 28, 0, 0, 0, tzinfo=dt.UTC)
    assert com2.submit_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com2.last_submit_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com2.order_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com2.last_update_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)

    assert com2.status == "PROCESSING"
    assert com2.reference == "CA/2022/9905"

    assert com3.is_active is True
    assert com3.finished is None
    assert com3.is_pesticide_on_free_sale_uk is False
    assert com3.is_manufacturer is True
    assert com3.product_name == "Another product"
    assert com3.chemical_name == "Another chemical"
    assert com3.manufacturing_process == "Test process"

    assert com3.exporter_id == 2
    assert com3.application_type_id == 2
    assert com3.created_by_id == 2
    assert com3.last_updated_by_id == 2
    assert com3.submitted_by_id is None

    assert com3.created == dt.datetime(2022, 4, 28, 0, 0, 0, tzinfo=dt.UTC)
    assert com3.submit_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com3.last_submit_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com3.order_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)
    assert com3.last_update_datetime == dt.datetime(2022, 4, 29, 0, 0, 0, tzinfo=dt.UTC)

    assert com3.status == "COMPLETED"
    assert com3.reference == "CA/2022/9906"

    assert web.CertificateOfFreeSaleApplication.objects.count() == 3
    cfs1, cfs2, cfs3 = web.CertificateOfFreeSaleApplication.objects.order_by("pk")

    ea7, ea8, ea9 = web.ExportApplication.objects.filter(
        process_ptr__process_type=ProcessTypes.CFS
    ).order_by("pk")

    assert ea7.countries.count() == 0
    assert ea8.countries.count() == 1
    assert ea9.countries.count() == 1

    assert ea7.reference == "CA/2022/9907"
    assert ea7.variation_requests.count() == 0
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9907)

    assert ea8.reference == "CA/2022/9908"
    assert ea8.variation_requests.count() == 0
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9908)

    assert ea9.reference == "CA/2022/9909/2"
    assert ea9.variation_requests.count() == 2
    assert web.UniqueReference.objects.get(prefix="CA", year=2022, reference=9909)

    vr2, vr3 = ea9.variation_requests.order_by("pk")
    assert vr2.what_varied == "Changes 2"
    assert vr2.requested_datetime == dt.datetime(2022, 10, 13, 11, 1, 5, tzinfo=dt.UTC)
    assert vr2.closed_datetime == dt.datetime(2022, 10, 14, 12, 1, 5, tzinfo=dt.UTC)
    assert vr3.what_varied == "Changes 3"
    assert vr3.requested_datetime == dt.datetime(2022, 10, 15, 11, 1, 5, tzinfo=dt.UTC)
    assert vr3.closed_datetime == dt.datetime(2022, 10, 16, 12, 1, 5, tzinfo=dt.UTC)

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
    assert ea8.further_information_requests.count() == 1
    assert ea9.further_information_requests.count() == 0

    fir2 = ea8.further_information_requests.first()
    assert fir2.status == "OPEN"

    case_note2, case_note3 = ea9.case_notes.order_by("pk")
    assert case_note2.files.count() == 0
    assert case_note3.files.count() == 2

    assert ea7.certificates.count() == 0
    assert ea8.certificates.count() == 1
    assert ea9.certificates.count() == 3

    assert list(ea7.cleared_by.values_list("id", flat=True)) == []
    assert list(ea8.cleared_by.values_list("id", flat=True)) == []
    assert list(ea9.cleared_by.values_list("id", flat=True).order_by("id")) == [2, 6]

    cert6 = ea8.certificates.first()
    cert7, cert8, cert9 = ea9.certificates.order_by("pk")

    assert list(cert6.cleared_by.values_list("id", flat=True)) == []
    assert list(cert7.cleared_by.values_list("id", flat=True)) == []
    assert list(cert8.cleared_by.values_list("id", flat=True)) == [2]
    assert list(cert9.cleared_by.values_list("id", flat=True).order_by("id")) == [2, 6]

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
    assert ref5.reference_data.country_id == 1
    assert ref5.check_code == "32415678"

    ref6 = cert9.document_references.first()
    assert ref6.reference == "CFS/2022/00002"
    assert ref6.reference_data.country_id == 1
    assert ref6.check_code == "32415679"
    assert web.UniqueReference.objects.get(prefix="CFS", year=2022, reference=1)

    assert cfs1.schedules.count() == 0
    assert cfs2.schedules.count() == 1
    assert cfs3.schedules.count() == 2
    assert web.UniqueReference.objects.get(prefix="CFS", year=2022, reference=2)

    sch1: web.CFSSchedule
    sch2: web.CFSSchedule
    sch3: web.CFSSchedule
    sch1 = cfs2.schedules.first()
    sch2, sch3 = cfs3.schedules.order_by("pk")

    assert sch1.product_eligibility == web.CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
    assert sch1.exporter_status == web.CFSSchedule.ExporterStatus.IS_MANUFACTURER
    assert sch1.brand_name_holder is None
    assert sch1.goods_placed_on_uk_market == "no"
    assert sch1.goods_export_only == "yes"
    assert sch1.any_raw_materials == "no"
    assert sch1.final_product_end_use is None
    assert sch1.country_of_manufacture_id == 1
    assert sch1.schedule_statements_accordance_with_standards is True
    assert sch1.schedule_statements_is_responsible_person is False
    assert sch1.manufacturer_name == "Manufacturer"
    assert sch1.manufacturer_address_entry_type == "SEARCH"
    assert sch1.legislations.count() == 0
    assert sch1.created_at == dt.datetime(2022, 11, 1, 12, 30, tzinfo=dt.UTC)
    assert sch1.updated_at == dt.datetime(2022, 11, 1, 12, 30, tzinfo=dt.UTC)
    assert sch1.is_biocidal() is False

    assert sch2.product_eligibility == web.CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET
    assert sch2.exporter_status == web.CFSSchedule.ExporterStatus.IS_NOT_MANUFACTURER
    assert sch2.brand_name_holder == "yes"
    assert sch2.goods_placed_on_uk_market == "yes"
    assert sch2.goods_export_only == "no"
    assert sch2.any_raw_materials == "yes"
    assert sch2.final_product_end_use == "A product"
    assert sch2.country_of_manufacture_id == 1
    assert sch2.schedule_statements_accordance_with_standards is False
    assert sch2.schedule_statements_is_responsible_person is True
    assert sch2.manufacturer_name is None
    assert sch2.manufacturer_address_entry_type == "SEARCH"
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

    # Testing Withdrawal
    ea10 = web.ExportApplication.objects.get(status="WITHDRAWN")
    assert ea10.withdrawals.count() == 3
    w1, w2, w3 = ea10.withdrawals.order_by("pk")

    assert w1.reason == "First reason"
    assert w1.status == "DELETED"
    assert w1.is_active is False
    assert w1.response == ""
    assert w1.response_by_id is None
    assert w1.created_datetime == dt.datetime(2024, 1, 31, 11, 27, 36, tzinfo=dt.UTC)
    assert w1.updated_datetime == dt.datetime(2024, 1, 31, 12, 27, 36, tzinfo=dt.UTC)

    assert w2.reason == "Second reason"
    assert w2.status == "REJECTED"
    assert w2.is_active is False
    assert w2.response == "Reject Reason"
    assert w2.response_by_id == 2
    assert w2.created_datetime == dt.datetime(2024, 1, 31, 13, 37, 36, tzinfo=dt.UTC)
    assert w2.updated_datetime == dt.datetime(2024, 1, 31, 13, 40, 00, tzinfo=dt.UTC)

    assert w3.reason == "Third reason"
    assert w3.status == "ACCEPTED"
    assert w3.is_active is False
    assert w3.response == ""
    assert w3.response_by_id == 2
    assert w3.created_datetime == dt.datetime(2024, 1, 31, 15, 00, 00, tzinfo=dt.UTC)
    assert w3.updated_datetime == dt.datetime(2024, 1, 31, 15, 10, 00, tzinfo=dt.UTC)

    # Certificate Application Templates
    assert web.CertificateApplicationTemplate.objects.count() == 2
    cat1 = web.CertificateApplicationTemplate.objects.get(application_type="CFS")

    assert cat1.name == "Template CFS"
    assert cat1.description == "A CFS Template"
    assert cat1.sharing == "PRIVATE"
    assert cat1.owner_id == 2
    assert cat1.created_datetime == dt.datetime(2023, 1, 2, 13, 23, tzinfo=dt.UTC)
    assert cat1.last_updated_datetime == dt.datetime(2023, 1, 2, 14, 23, tzinfo=dt.UTC)

    cfs_cat = web.CertificateOfFreeSaleApplicationTemplate.objects.first()
    assert list(cfs_cat.countries.values_list("pk", flat=True).order_by("pk")) == [1, 2]
    assert cfs_cat.last_update_datetime == dt.datetime(2023, 1, 2, 14, 23, tzinfo=dt.UTC)
    assert cfs_cat.schedules.count() == 2

    sch_t1: web.CFSScheduleTemplate
    sch_t1, sch_t2 = cfs_cat.schedules.order_by("pk")

    assert sch_t1.exporter_status == "MANUFACTURER"
    assert sch_t1.brand_name_holder == "yes"
    assert sch_t1.biocidal_claim == "no"
    assert sch_t1.product_eligibility == "MEET_UK_PRODUCT_SAFETY"
    assert sch_t1.goods_placed_on_uk_market == "no"
    assert sch_t1.goods_export_only == "yes"
    assert sch_t1.any_raw_materials == "yes"
    assert sch_t1.final_product_end_use == "Test End Use"
    assert sch_t1.country_of_manufacture_id == 1
    assert sch_t1.schedule_statements_accordance_with_standards is False
    assert sch_t1.schedule_statements_is_responsible_person is True
    assert sch_t1.manufacturer_name == "Test Manufacturer"
    assert sch_t1.manufacturer_address_entry_type == "SEARCH"
    assert sch_t1.manufacturer_postcode == "Test Postcode"
    assert sch_t1.manufacturer_address == "Test Address"
    assert sch_t1.created_by_id == 2
    assert sch_t1.created_at == dt.datetime(2023, 1, 2, 14, 23, tzinfo=dt.UTC)
    assert sch_t1.updated_at == dt.datetime(2023, 1, 2, 14, 23, tzinfo=dt.UTC)
    assert list(sch_t1.legislations.values_list("pk", flat=True).order_by("pk")) == [1, 3]

    assert sch_t1.products.count() == 3
    assert list(sch_t1.products.values_list("product_name", flat=True).order_by("pk")) == [
        "Product A",
        "Product B",
        "Product C",
    ]

    assert list(sch_t2.products.values_list("product_name", flat=True).order_by("pk")) == [
        "Product A",
        "Product B",
    ]
    p1, p2 = sch_t2.products.order_by("pk")

    p1.active_ingredients.count() == 2
    ai1, ai2 = p1.active_ingredients.order_by("pk")
    assert ai1.name == "AI 1"
    assert ai1.cas_number == "12-34-5"
    assert ai2.name == "AI 2"
    assert ai2.cas_number == "22-34-5"

    assert p2.active_ingredients.count() == 1
    ai3 = p2.active_ingredients.first()
    assert ai3.name == "AI 3"
    assert ai3.cas_number == "32-34-5"

    assert p1.product_type_numbers.count() == 2
    assert list(p1.product_type_numbers.values_list("product_type_number", flat=True)) == [1, 2]
    assert p2.product_type_numbers.count() == 1
    assert p2.product_type_numbers.first().product_type_number == 3

    cat2 = web.CertificateApplicationTemplate.objects.get(application_type="COM")

    assert cat2.name == "Template COM"
    assert cat2.description == "A COM Template"
    assert cat2.sharing == "EDIT"
    assert cat2.owner_id == 2
    assert cat2.created_datetime == dt.datetime(2023, 1, 3, 13, 23, tzinfo=dt.UTC)
    assert cat2.last_updated_datetime == dt.datetime(2023, 1, 3, 14, 23, tzinfo=dt.UTC)

    com_cat = web.CertificateOfManufactureApplicationTemplate.objects.first()
    assert list(com_cat.countries.values_list("pk", flat=True).order_by("pk")) == [1, 2]
    assert com_cat.last_update_datetime == dt.datetime(2023, 1, 2, 14, 23, tzinfo=dt.UTC)
    assert com_cat.is_manufacturer is True
    assert com_cat.is_pesticide_on_free_sale_uk is False
    assert com_cat.product_name == "Test product"
    assert com_cat.chemical_name == "Test chemical"
    assert com_cat.manufacturing_process == "Test manufacturing process"
