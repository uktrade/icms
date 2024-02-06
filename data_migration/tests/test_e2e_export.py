import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command

from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands._types import QueryModel
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
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

    assert web.CertificateOfGoodManufacturingPracticeApplication.objects.count() == 4
    ea1, ea2, ea3, _ = web.ExportApplication.objects.filter(
        process_ptr__process_type=ProcessTypes.GMP
    ).order_by("pk")

    assert ea1.countries.count() == 0
    assert ea2.countries.count() == 3
    assert ea3.countries.count() == 1

    assert ea1.variation_requests.count() == 0
    assert ea2.variation_requests.count() == 0
    assert ea3.variation_requests.count() == 1

    vr1: web.VariationRequest = ea3.variation_requests.first()
    assert vr1.what_varied == "Changes 1"
    assert vr1.requested_datetime == dt.datetime(2022, 10, 13, 10, 1, 5, tzinfo=dt.timezone.utc)
    assert vr1.closed_datetime == dt.datetime(2022, 10, 14, 11, 1, 5, tzinfo=dt.timezone.utc)

    assert ea1.update_requests.count() == 0
    assert ea2.update_requests.count() == 1
    assert ea3.update_requests.count() == 0

    assert ea1.case_notes.count() == 0
    assert ea2.case_notes.count() == 2
    assert ea2.case_notes.filter(is_active=True).count() == 1
    assert ea2.case_notes.filter(is_active=False).count() == 1
    assert ea3.case_notes.count() == 0

    assert ea1.case_emails.count() == 0
    assert ea2.case_emails.count() == 0
    assert ea3.case_emails.count() == 2

    assert ea1.further_information_requests.count() == 0
    assert ea2.further_information_requests.count() == 0
    assert ea3.further_information_requests.count() == 0

    case_note1 = ea2.case_notes.filter(is_active=True).first()
    assert case_note1.note == "This is a case note"
    assert case_note1.create_datetime == dt.datetime(2022, 9, 20, 7, 31, 34, tzinfo=dt.timezone.utc)
    assert case_note1.created_by_id == 2
    assert case_note1.updated_at == dt.datetime(2022, 9, 20, 7, 31, 34, tzinfo=dt.timezone.utc)
    assert case_note1.updated_by_id == 2
    assert case_note1.files.count() == 1

    case_note4 = ea2.case_notes.filter(is_active=False).first()
    assert case_note4.note == "This is a deleted case note"

    assert ea1.certificates.count() == 0
    assert ea2.certificates.count() == 1
    assert ea3.certificates.count() == 2

    assert list(ea1.cleared_by.values_list("id", flat=True)) == []
    assert list(ea2.cleared_by.values_list("id", flat=True)) == []
    assert list(ea2.cleared_by.values_list("id", flat=True)) == []

    cert1 = ea2.certificates.first()
    cert2, cert3 = ea3.certificates.order_by("pk")

    assert list(cert1.cleared_by.values_list("id", flat=True)) == []
    assert list(cert2.cleared_by.values_list("id", flat=True)) == []
    assert list(cert3.cleared_by.values_list("id", flat=True)) == []

    assert cert1.status == "DR"
    assert cert1.created_at == dt.datetime(2022, 4, 29, 12, 21, tzinfo=dt.timezone.utc)
    assert cert2.status == "AR"
    assert cert2.document_references.count() == 0
    assert cert3.status == "AC"
    assert cert3.document_references.count() == 1

    refs = cert1.document_references.order_by("pk")
    ref2 = cert3.document_references.first()

    assert refs.count() == 3
    assert refs[0].reference == "GMP/2022/00001"
    assert refs[0].reference_data.country_id == 1
    assert refs[0].check_code == "12345678"

    assert refs[1].reference == "GMP/2022/00002"
    assert refs[1].reference_data.country_id == 2
    assert refs[1].check_code == "56781234"

    assert refs[2].reference == "GMP/2022/00003"
    assert refs[2].reference_data.country_id == 3
    assert refs[2].check_code == "43215678"

    assert ref2.reference == "GMP/2022/00004"
    assert ref2.reference_data.country_id == 1
    assert ref2.check_code == "87654321"

    gmp1, gmp2, gmp3, _ = web.CertificateOfGoodManufacturingPracticeApplication.objects.order_by(
        "pk"
    )

    assert gmp1.supporting_documents.count() == 1
    assert gmp1.supporting_documents.first().file_type == "BRC_GSOCP"
    assert gmp1.brand_name is None
    assert gmp1.gmp_certificate_issued is None

    assert gmp2.supporting_documents.count() == 2
    assert gmp2.supporting_documents.filter(file_type="ISO_22716").count() == 1
    assert gmp2.supporting_documents.filter(file_type="ISO_17065").count() == 1
    assert gmp2.brand_name == "A brand"
    assert (
        gmp2.gmp_certificate_issued
        == web.CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.BRC_GSOCP
    )

    assert gmp3.supporting_documents.count() == 1
    assert gmp3.supporting_documents.first().file_type == "ISO_17021"
    assert gmp3.brand_name == "Another brand"
    assert (
        gmp3.gmp_certificate_issued
        == web.CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.ISO_22716
    )

    assert web.CertificateOfManufactureApplication.objects.count() == 3
    com1, com2, com3 = web.CertificateOfManufactureApplication.objects.order_by("pk")

    ea4, ea5, ea6 = web.ExportApplication.objects.filter(
        process_ptr__process_type=ProcessTypes.COM
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
    assert cert5.status == "AC"
    assert cert5.document_references.count() == 1

    ref3 = cert4.document_references.first()
    ref4 = cert5.document_references.first()

    assert ref3.reference == "COM/2022/00001"
    assert ref3.reference_data.country_id == 1
    assert ref3.check_code == "87651432"

    assert ref4.reference == "COM/2022/00002"
    assert ref4.reference_data.country_id == 1
    assert ref4.check_code == "87651432"

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
        process_ptr__process_type=ProcessTypes.CFS
    ).order_by("pk")

    assert ea7.countries.count() == 0
    assert ea8.countries.count() == 1
    assert ea9.countries.count() == 1

    assert ea7.variation_requests.count() == 0
    assert ea8.variation_requests.count() == 0
    assert ea9.variation_requests.count() == 2

    vr2, vr3 = ea9.variation_requests.order_by("pk")
    assert vr2.what_varied == "Changes 2"
    assert vr2.requested_datetime == dt.datetime(2022, 10, 13, 10, 1, 5, tzinfo=dt.timezone.utc)
    assert vr2.closed_datetime == dt.datetime(2022, 10, 14, 11, 1, 5, tzinfo=dt.timezone.utc)
    assert vr3.what_varied == "Changes 3"
    assert vr3.requested_datetime == dt.datetime(2022, 10, 15, 10, 1, 5, tzinfo=dt.timezone.utc)
    assert vr3.closed_datetime == dt.datetime(2022, 10, 16, 11, 1, 5, tzinfo=dt.timezone.utc)

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

    assert cfs1.schedules.count() == 0
    assert cfs2.schedules.count() == 1
    assert cfs3.schedules.count() == 2

    sch1 = cfs2.schedules.first()
    sch2, sch3 = cfs3.schedules.order_by("pk")

    assert sch1.legislations.count() == 0
    assert sch1.created_at == dt.datetime(2022, 11, 1, 12, 30, tzinfo=dt.timezone.utc)
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
