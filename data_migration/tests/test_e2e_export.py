from unittest import mock

import cx_Oracle
import pytest
from django.core.management import call_command

from data_migration import models as dm
from data_migration.queries import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
from data_migration.queries import export_application as q_ex
from data_migration.queries import files as q_f
from data_migration.queries import reference as q_ref
from data_migration.queries import user as q_u
from data_migration.utils import xml_parser
from web import models as web

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


@pytest.mark.django_db
@mock.patch.object(cx_Oracle, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, export_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, export_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, export_query_model)
@mock.patch.dict(DATA_TYPE_XML, export_xml)
def test_import_export_data(mock_connect, dummy_dm_settings):
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
