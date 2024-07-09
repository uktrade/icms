import datetime as dt
import io
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from django.conf import settings

from web.domains.case.services import document_pack
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    DFLApplication,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    Template,
    WoodQuotaApplication,
    WoodQuotaChecklist,
)
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, StaticPdfGenerator, utils


@pytest.fixture(autouse=True)
def mock_get_licence_endorsements(monkeypatch):
    mock_get_licence_endorsements = create_autospec(utils.get_licence_endorsements)
    mock_get_licence_endorsements.return_value = []
    monkeypatch.setattr(utils, "get_licence_endorsements", mock_get_licence_endorsements)


@pytest.mark.parametrize(
    "AppCls,doc_type,expected_template",
    [
        (
            OpenIndividualLicenceApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-oil-licence.html",
        ),
        (
            OpenIndividualLicenceApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-oil-licence.html",
        ),
        (
            DFLApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-dfl-licence.html",
        ),
        (
            DFLApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-dfl-licence.html",
        ),
        (
            SILApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-sil-licence.html",
        ),
        (
            SILApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-sil-licence.html",
        ),
        (
            SanctionsAndAdhocApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/sanctions-licence.html",
        ),
        (
            SanctionsAndAdhocApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/sanctions-licence.html",
        ),
        (
            SILApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-sil-licence.html",
        ),
        (
            WoodQuotaApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/wood-licence.html",
        ),
        (
            WoodQuotaApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/wood-licence.html",
        ),
        # All other licence types use the default for LICENCE_PREVIEW
        (
            OpenIndividualLicenceApplication,
            DocumentTypes.COVER_LETTER_PREVIEW,
            "pdf/import/cover-letter.html",
        ),
        (
            OpenIndividualLicenceApplication,
            DocumentTypes.COVER_LETTER_PRE_SIGN,
            "pdf/import/cover-letter.html",
        ),
        # Export Certificates
        (
            CertificateOfFreeSaleApplication,
            DocumentTypes.CERTIFICATE_PREVIEW,
            "pdf/export/cfs-certificate.html",
        ),
        (
            CertificateOfFreeSaleApplication,
            DocumentTypes.CERTIFICATE_PRE_SIGN,
            "pdf/export/cfs-certificate.html",
        ),
        (
            CertificateOfManufactureApplication,
            DocumentTypes.CERTIFICATE_PREVIEW,
            "pdf/export/com-certificate.html",
        ),
        (
            CertificateOfManufactureApplication,
            DocumentTypes.CERTIFICATE_PRE_SIGN,
            "pdf/export/com-certificate.html",
        ),
        (
            CertificateOfGoodManufacturingPracticeApplication,
            DocumentTypes.CERTIFICATE_PREVIEW,
            "pdf/export/gmp-certificate.html",
        ),
        (
            CertificateOfGoodManufacturingPracticeApplication,
            DocumentTypes.CERTIFICATE_PRE_SIGN,
            "pdf/export/gmp-certificate.html",
        ),
    ],
)
def test_get_template(AppCls, doc_type, expected_template, licence):
    app = AppCls(process_type=AppCls.PROCESS_TYPE)
    generator = PdfGenerator(doc_type, app, licence)
    actual_template = generator.get_template()

    assert expected_template == actual_template


def get_static_cfs_cover_letter_template():
    generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
    template = generator.get_template()
    assert template == "pdf/export/cfs-letter.html"


def get_static_doc_template():
    generator = StaticPdfGenerator(DocumentTypes.CERTIFICATE_PRE_SIGN)
    with pytest.raises(
        ValueError, match=f"Unsupported document type: {DocumentTypes.CERTIFICATE_PRE_SIGN}"
    ):
        generator.get_template()


def test_get_template_raises_error_if_doc_type_unsupported(licence):
    app = OpenIndividualLicenceApplication(process_type="Invalid process type")
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, app, licence)

    with pytest.raises(ValueError, match="Unsupported process type"):
        generator.get_template()


def test_get_fa_oil_preview_licence_context(oil_app, licence, oil_expected_preview_context):
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, oil_app, licence)

    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_licence_number", return_value="0000001B")
def test_get_fa_oil_licence_pre_sign_context(
    licence_mock, oil_app, licence, oil_expected_preview_context
):
    generator = PdfGenerator(DocumentTypes.LICENCE_PRE_SIGN, oil_app, licence)

    oil_expected_preview_context["preview_licence"] = False
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app
    oil_expected_preview_context["licence_number"] = "0000001B"

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_fa_dfl_goods")
def test_get_fa_dfl_preview_licence_context(
    mock_get_goods, dfl_app, licence, dfl_expected_preview_context
):
    mock_get_goods.return_value = ["goods one", "goods two", "goods three"]

    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, dfl_app, licence)

    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["preview_licence"] = True
    dfl_expected_preview_context["paper_licence_only"] = False
    dfl_expected_preview_context["process"] = dfl_app

    actual_context = generator.get_document_context()

    assert dfl_expected_preview_context == actual_context


@patch.multiple(
    "web.utils.pdf.utils",
    _get_fa_dfl_goods=MagicMock(return_value=["goods one", "goods two", "goods three"]),
    _get_licence_number=MagicMock(return_value="0000001B"),
)
def test_get_fa_dfl_licence_pre_sign_context(
    dfl_app, licence, dfl_expected_preview_context, **mocks
):
    generator = PdfGenerator(DocumentTypes.LICENCE_PRE_SIGN, dfl_app, licence)

    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["preview_licence"] = False
    dfl_expected_preview_context["paper_licence_only"] = False
    dfl_expected_preview_context["process"] = dfl_app
    dfl_expected_preview_context["licence_number"] = "0000001B"

    actual_context = generator.get_document_context()

    assert dfl_expected_preview_context == actual_context


@pytest.mark.django_db
@patch("web.utils.pdf.utils._get_fa_sil_goods")
def test_get_fa_sil_preview_licence_context(
    mock_get_goods, sil_app, licence, sil_expected_preview_context
):
    mock_get_goods.return_value = [("goods one", 10), ("goods two", 20), ("goods three", 30)]
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, sil_app, licence)
    sil_app.manufactured = True
    template = Template.objects.get(template_code="FIREARMS_MARKINGS_NON_STANDARD")

    sil_expected_preview_context["goods"] = [
        ("goods one", 10),
        ("goods two", 20),
        ("goods three", 30),
    ]
    sil_expected_preview_context["preview_licence"] = True
    sil_expected_preview_context["paper_licence_only"] = False
    sil_expected_preview_context["process"] = sil_app
    sil_expected_preview_context["markings_text"] = template.template_content

    actual_context = generator.get_document_context()

    assert sil_expected_preview_context == actual_context


@pytest.mark.django_db
@patch.multiple(
    "web.utils.pdf.utils",
    _get_fa_sil_goods=MagicMock(
        return_value=[("goods one", 10), ("goods two", 20), ("goods three", 30)]
    ),
    _get_licence_number=MagicMock(return_value="0000001B"),
)
def test_get_fa_sil_licence_pre_sign_context(sil_app, licence, sil_expected_preview_context):
    generator = PdfGenerator(DocumentTypes.LICENCE_PRE_SIGN, sil_app, licence)

    sil_expected_preview_context["goods"] = [
        ("goods one", 10),
        ("goods two", 20),
        ("goods three", 30),
    ]
    sil_expected_preview_context["preview_licence"] = False
    sil_expected_preview_context["paper_licence_only"] = False
    sil_expected_preview_context["process"] = sil_app
    sil_expected_preview_context["licence_number"] = "0000001B"

    actual_context = generator.get_document_context()

    assert sil_expected_preview_context == actual_context


def test_get_sanctions_preview_licence_context(
    sanctions_app_submitted, sanctions_expected_preview_context
):
    app = sanctions_app_submitted
    licence = app.licences.first()
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, app, licence)

    expected_context = sanctions_expected_preview_context | {
        "process": app,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


def test_get_sanctions_pre_sign_licence_context(
    sanctions_app_submitted, sanctions_expected_preview_context, ilb_admin_client
):
    app = sanctions_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.decision = app.APPROVE
    app.save()

    licence = app.licences.first()
    licence.case_completion_datetime = dt.datetime(2023, 9, 1, tzinfo=dt.UTC)
    licence.licence_start_date = dt.date(2023, 9, 1)
    licence.licence_end_date = dt.date(2024, 3, 1)
    licence.issue_paper_licence_only = False
    licence.save()

    ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    licence.refresh_from_db()

    generator = PdfGenerator(DocumentTypes.LICENCE_PRE_SIGN, app, licence)

    expected_context = sanctions_expected_preview_context | {
        "preview_licence": False,
        "process": app,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "licence_number": "GBSAN0000001B",
        "licence_end_date": "1st March 2024",
        "licence_start_date": "1st September 2023",
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


def test_get_wood_preview_licence_context(wood_app_submitted, wood_expected_preview_context):
    app = wood_app_submitted
    licence = app.licences.first()
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, app, licence)

    expected_context = wood_expected_preview_context | {
        "process": app,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


def test_get_wood_pre_sign_licence_context(
    wood_app_submitted, wood_expected_preview_context, ilb_admin_client
):
    app = wood_app_submitted
    licence = app.licences.first()

    app.refresh_from_db()
    app.decision = app.APPROVE
    app.save()

    licence = app.licences.first()
    licence.case_completion_datetime = dt.datetime(2023, 9, 1, tzinfo=dt.UTC)
    licence.licence_start_date = dt.date(2023, 9, 1)
    licence.licence_end_date = dt.date(2024, 3, 1)
    licence.issue_paper_licence_only = True
    licence.save()

    WoodQuotaChecklist.objects.create(
        **{
            "import_application": app,
            "case_update": YesNoNAChoices.yes,
            "fir_required": YesNoNAChoices.yes,
            "response_preparation": True,
            "validity_period_correct": YesNoNAChoices.yes,
            "endorsements_listed": YesNoNAChoices.yes,
            "authorisation": True,
            "sigl_wood_application_logged": True,
        }
    )

    ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    licence.refresh_from_db()
    generator = PdfGenerator(DocumentTypes.LICENCE_PRE_SIGN, app, licence)

    expected_context = wood_expected_preview_context | {
        "preview_licence": False,
        "process": app,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "licence_number": "0000001B",
        "licence_end_date": "1st March 2024",
        "licence_start_date": "1st September 2023",
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


@patch("web.utils.pdf.utils.get_active_signature_file")
def test_get_preview_cover_letter_context(patched_get_active_signature_file, licence):
    magic_mock = MagicMock()
    patched_get_active_signature_file.return_value = (magic_mock, "A")
    app = DFLApplication(process_type=DFLApplication.PROCESS_TYPE)
    app.cover_letter_text = "ABC"

    generator = PdfGenerator(DocumentTypes.COVER_LETTER_PREVIEW, app, licence)

    expected_context = {
        "process": app,
        "content": "ABC",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": dt.date.today().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": True,
        "ilb_contact_address_split": [
            "Import Licencing Branch",
            "Queensway House",
            "West Precinct",
            "Billingham",
            "TS23 2NF",  # /PS-IGNORE
        ],
        "signature": magic_mock,
        "signature_file": "A",
    }

    actual_context = generator.get_document_context()

    assert expected_context == actual_context


@patch("web.utils.pdf.utils.get_active_signature_file")
def test_get_pre_sign_cover_letter_context(patched_get_active_signature_file, licence):
    magic_mock = MagicMock()
    patched_get_active_signature_file.return_value = (magic_mock, "A")
    app = DFLApplication(process_type=DFLApplication.PROCESS_TYPE)
    app.cover_letter_text = "ABC"

    generator = PdfGenerator(DocumentTypes.COVER_LETTER_PRE_SIGN, app, licence)

    expected_context = {
        "process": app,
        "content": "ABC",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": dt.date.today().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": False,
        "ilb_contact_address_split": [
            "Import Licencing Branch",
            "Queensway House",
            "West Precinct",
            "Billingham",
            "TS23 2NF",  # /PS-IGNORE
        ],
        "signature": magic_mock,
        "signature_file": "A",
    }

    actual_context = generator.get_document_context()

    assert expected_context == actual_context


def test_get_document_context_raises_error_if_process_type_unsupported(licence):
    app = OpenIndividualLicenceApplication(process_type="INVALID_PROCESS_TYPE")

    with pytest.raises(ValueError, match="Unsupported process type"):
        generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, app, licence)
        generator.get_document_context()


def test_get_pdf(db, oil_app, licence):
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, oil_app, licence)
    pdf_file = generator.get_pdf()

    # This tests doesn't actually do a great deal other than check it creates
    # a pdf, however all the methods have already been tested.
    assert pdf_file.startswith(b"%PDF-")


def test_get_preview_cfs_certificate_context(cfs_app_submitted):
    app = cfs_app_submitted
    country = app.countries.first()
    certificate = app.certificates.first()
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PREVIEW, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is True
    assert context["schedule_text"]
    assert context["statement_translations"] == []
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == "[[CERTIFICATE_REFERENCE]]"


def test_get_preview_com_certificate_context(com_app_submitted):
    app = com_app_submitted
    country = app.countries.first()
    certificate = app.certificates.first()
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PREVIEW, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is True
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == "[[CERTIFICATE_REFERENCE]]"
    assert context["product_name"] == app.product_name


def test_get_preview_gmp_certifcate_context(gmp_app_submitted):
    app = gmp_app_submitted
    country = app.countries.first()
    certificate = app.certificates.first()
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PREVIEW, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is True
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == "[[CERTIFICATE_REFERENCE]]"
    assert context["brand_name"] == "A Brand"


def test_get_pre_sign_cfs_certificate_context(completed_cfs_app):
    app = completed_cfs_app
    country = app.countries.first()
    certificate = app.certificates.first()
    document = document_pack.doc_ref_certificate_get(certificate, country)
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PRE_SIGN, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is False
    assert context["schedule_text"]
    assert context["statement_translations"] == []
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == document.reference
    assert context["certificate_code"] == document.check_code
    assert context["qr_img_base64"].startswith("iVBORw")


def test_get_pre_sign_com_certificate_context(completed_com_app):
    app = completed_com_app
    country = app.countries.first()
    certificate = app.certificates.first()
    document = document_pack.doc_ref_certificate_get(certificate, country)
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PRE_SIGN, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is False
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["product_name"] == app.product_name
    assert context["reference"] == document.reference
    assert context["certificate_code"] == document.check_code
    assert context["qr_img_base64"].startswith("iVBORw")


def test_get_pre_sign_gmp_certifcate_context(completed_gmp_app):
    app = completed_gmp_app
    country = app.countries.first()
    certificate = app.certificates.first()
    document = document_pack.doc_ref_certificate_get(certificate, country)
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PRE_SIGN, app, certificate, country)

    context = generator.get_document_context()

    assert context["preview"] is False
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["brand_name"] == "A Brand"
    assert context["reference"] == document.reference
    assert context["certificate_code"] == document.check_code
    assert context["qr_img_base64"].startswith("iVBORw")


def test_certificate_no_country_get_document_context_invalid(cfs_app_submitted):
    app = cfs_app_submitted
    certificate = app.certificates.first()
    generator = PdfGenerator(DocumentTypes.CERTIFICATE_PREVIEW, app, certificate)

    with pytest.raises(ValueError, match="Country must be specified for export certificates"):
        generator.get_document_context()


def test_get_cfs_cover_letter_certificate_context():
    generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
    context = generator.get_document_context()

    assert context == {
        "ilb_contact_address_split": settings.ILB_CONTACT_ADDRESS.split(", "),
        "ilb_contact_name": settings.ILB_CONTACT_NAME,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }


def test_get_cfs_cover_letter_certificate_context_invalid_doc_type():
    generator = StaticPdfGenerator(DocumentTypes.CERTIFICATE_PREVIEW)

    with pytest.raises(
        ValueError, match=f"Unsupported document type: {DocumentTypes.CERTIFICATE_PREVIEW}"
    ):
        generator.get_document_context()


@patch("web.utils.pdf.generator.PdfGenerator.get_document_html", return_value="<html>test</html>")
@patch("playwright.sync_api.Page.set_content")
def test_playwright_used(mocked_page_object, mocked_get_document_html, oil_app, licence):
    target = io.BytesIO()
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, oil_app, licence)
    generator.get_pdf(target=target)
    assert mocked_page_object.called_with("<html>test</html>")
    assert target.getvalue().startswith(b"%PDF-")


def test_get_pdf_returns_bytes(oil_app, licence):
    generator = PdfGenerator(DocumentTypes.LICENCE_PREVIEW, oil_app, licence)
    pdf_file = generator.get_pdf()
    assert isinstance(pdf_file, bytes)
    assert pdf_file.startswith(b"%PDF-")
