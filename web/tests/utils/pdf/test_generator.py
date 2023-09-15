import datetime
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from django.conf import settings

from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfManufactureApplication,
    DFLApplication,
    OpenIndividualLicenceApplication,
    SILApplication,
    Template,
    WoodQuotaApplication,
)
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, utils


# TODO: Revisit when doing ICMSLST-1428
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
            "pdf/import/fa-oil-licence-preview.html",
        ),
        (
            OpenIndividualLicenceApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-oil-licence-pre-sign.html",
        ),
        (
            DFLApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-dfl-licence-preview.html",
        ),
        (
            DFLApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-dfl-licence-pre-sign.html",
        ),
        (
            SILApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-sil-licence-preview.html",
        ),
        (
            SILApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-sil-licence-pre-sign.html",
        ),
        # All other licence types use the default for LICENCE_PREVIEW
        (
            WoodQuotaApplication,
            DocumentTypes.LICENCE_PREVIEW,
            "web/domains/case/import/manage/preview-licence.html",
        ),
        (
            WoodQuotaApplication,
            DocumentTypes.LICENCE_PRE_SIGN,
            "web/domains/case/import/manage/preview-licence.html",
        ),
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
    ],
)
def test_get_template(AppCls, doc_type, expected_template, licence):
    app = AppCls(process_type=AppCls.PROCESS_TYPE)
    generator = PdfGenerator(app, licence, doc_type)
    actual_template = generator.get_template()

    assert expected_template == actual_template


def test_get_template_raises_error_if_doc_type_unsupported(licence):
    app = OpenIndividualLicenceApplication(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE
    )
    generator = PdfGenerator(app, licence, "INVALID_DOC_TYPE")

    with pytest.raises(ValueError, match="Unsupported document type"):
        generator.get_template()


def test_get_fa_oil_preview_licence_context(oil_app, licence, oil_expected_preview_context):
    generator = PdfGenerator(oil_app, licence, DocumentTypes.LICENCE_PREVIEW)

    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_licence_number", return_value="0000001B")
def test_get_fa_oil_licence_pre_sign_context(
    licence_mock, oil_app, licence, oil_expected_preview_context
):
    generator = PdfGenerator(oil_app, licence, DocumentTypes.LICENCE_PRE_SIGN)

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

    generator = PdfGenerator(dfl_app, licence, DocumentTypes.LICENCE_PREVIEW)

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
    generator = PdfGenerator(dfl_app, licence, DocumentTypes.LICENCE_PRE_SIGN)

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
    generator = PdfGenerator(sil_app, licence, DocumentTypes.LICENCE_PREVIEW)
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
    generator = PdfGenerator(sil_app, licence, DocumentTypes.LICENCE_PRE_SIGN)

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


# TODO: Remove the default tests when every app type has been implemented
def test_get_default_preview_licence_context(licence):
    app = WoodQuotaApplication(process_type=WoodQuotaApplication.PROCESS_TYPE)

    generator = PdfGenerator(app, licence, DocumentTypes.LICENCE_PREVIEW)

    expected_context = {
        "process": app,
        "page_title": "Licence Preview",
        "preview_licence": True,
        "paper_licence_only": False,
        "issue_date": datetime.date.today().strftime("%d %B %Y"),
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


def test_get_preview_cover_letter_context(licence):
    app = DFLApplication(process_type=DFLApplication.PROCESS_TYPE)
    app.cover_letter_text = "ABC"

    generator = PdfGenerator(app, licence, DocumentTypes.COVER_LETTER_PREVIEW)

    expected_context = {
        "process": app,
        "content": "ABC",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": datetime.date.today().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": True,
    }

    actual_context = generator.get_document_context()

    assert expected_context == actual_context


def test_get_pre_sign_cover_letter_context(licence):
    app = DFLApplication(process_type=DFLApplication.PROCESS_TYPE)
    app.cover_letter_text = "ABC"

    generator = PdfGenerator(app, licence, DocumentTypes.COVER_LETTER_PRE_SIGN)

    expected_context = {
        "process": app,
        "content": "ABC",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": datetime.date.today().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": False,
    }

    actual_context = generator.get_document_context()

    assert expected_context == actual_context


def test_get_document_context_raises_error_if_doc_type_unsupported(licence):
    app = OpenIndividualLicenceApplication(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE
    )

    with pytest.raises(ValueError, match="Unsupported document type"):
        generator = PdfGenerator(app, licence, "INVALID_DOC_TYPE")
        generator.get_document_context()


def test_get_pdf(oil_app, licence):
    generator = PdfGenerator(oil_app, licence, DocumentTypes.LICENCE_PREVIEW)
    pdf_file = generator.get_pdf()

    # This tests doesn't actually do a great deal other than check it creates
    # a pdf, however all the methods have already been tested.
    assert pdf_file.startswith(b"%PDF-")


def test_get_preview_cfs_certificate_context(cfs_app_submitted):
    app = cfs_app_submitted
    country = app.countries.first()
    certificate = app.certificates.first()
    generator = PdfGenerator(app, certificate, DocumentTypes.CERTIFICATE_PREVIEW, country)

    context = generator.get_document_context()

    assert context["preview"] is True
    assert context["schedule_paragraphs"]
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == "[[CERTIFICATE_REFERENCE]]"


def test_get_preview_com_certificate_context(com_app_submitted):
    app = com_app_submitted
    country = app.countries.first()
    certificate = app.certificates.first()
    generator = PdfGenerator(app, certificate, DocumentTypes.CERTIFICATE_PREVIEW, country)

    context = generator.get_document_context()

    assert context["preview"] is True
    assert context["exporter_name"] == app.exporter.name.upper()
    assert context["reference"] == "[[CERTIFICATE_REFERENCE]]"


def test_certificate_no_country_get_document_context_invalid(cfs_app_submitted):
    app = cfs_app_submitted
    certificate = app.certificates.first()
    generator = PdfGenerator(app, certificate, DocumentTypes.CERTIFICATE_PREVIEW)

    with pytest.raises(ValueError, match="Country must be specified for export certificates"):
        generator.get_document_context()
