import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.fa_sil.models import SILApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.utils.pdf import PdfGenerator, types


@pytest.mark.parametrize(
    "AppCls,doc_type,expected_template",
    [
        (
            OpenIndividualLicenceApplication,
            types.DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-oil-licence-preview.html",
        ),
        (
            OpenIndividualLicenceApplication,
            types.DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-oil-licence-pre-sign.html",
        ),
        (
            DFLApplication,
            types.DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-dfl-licence-preview.html",
        ),
        (
            DFLApplication,
            types.DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-dfl-licence-pre-sign.html",
        ),
        (
            SILApplication,
            types.DocumentTypes.LICENCE_PREVIEW,
            "pdf/import/fa-sil-licence-preview.html",
        ),
        (
            SILApplication,
            types.DocumentTypes.LICENCE_PRE_SIGN,
            "pdf/import/fa-sil-licence-pre-sign.html",
        ),
        # All other licence types use the default for LICENCE_PREVIEW
        (
            WoodQuotaApplication,
            types.DocumentTypes.LICENCE_PREVIEW,
            "web/domains/case/import/manage/preview-licence.html",
        ),
        (
            WoodQuotaApplication,
            types.DocumentTypes.LICENCE_PRE_SIGN,
            "web/domains/case/import/manage/preview-licence.html",
        ),
        # All licence types use the default for COVER_LETTER currently
        (
            OpenIndividualLicenceApplication,
            types.DocumentTypes.COVER_LETTER,
            "web/domains/case/import/manage/preview-cover-letter.html",
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
    generator = PdfGenerator(oil_app, licence, types.DocumentTypes.LICENCE_PREVIEW)

    oil_expected_preview_context["page_title"] = "Licence Preview"
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_licence_number", return_value="0000001B")
def test_get_fa_oil_licence_pre_sign_context(
    licence_mock, oil_app, licence, oil_expected_preview_context
):
    generator = PdfGenerator(oil_app, licence, types.DocumentTypes.LICENCE_PRE_SIGN)

    oil_expected_preview_context["page_title"] = "Licence Preview"
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

    generator = PdfGenerator(dfl_app, licence, types.DocumentTypes.LICENCE_PREVIEW)

    dfl_expected_preview_context["page_title"] = "Licence Preview"
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
    generator = PdfGenerator(dfl_app, licence, types.DocumentTypes.LICENCE_PRE_SIGN)

    dfl_expected_preview_context["page_title"] = "Licence Preview"
    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["preview_licence"] = False
    dfl_expected_preview_context["paper_licence_only"] = False
    dfl_expected_preview_context["process"] = dfl_app
    dfl_expected_preview_context["licence_number"] = "0000001B"

    actual_context = generator.get_document_context()

    assert dfl_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_fa_sil_goods")
def test_get_fa_sil_preview_licence_context(
    mock_get_goods, sil_app, licence, sil_expected_preview_context
):
    mock_get_goods.return_value = [("goods one", 10), ("goods two", 20), ("goods three", 30)]

    generator = PdfGenerator(sil_app, licence, types.DocumentTypes.LICENCE_PREVIEW)

    sil_expected_preview_context["page_title"] = "Licence Preview"
    sil_expected_preview_context["goods"] = [
        ("goods one", 10),
        ("goods two", 20),
        ("goods three", 30),
    ]
    sil_expected_preview_context["preview_licence"] = True
    sil_expected_preview_context["paper_licence_only"] = False
    sil_expected_preview_context["process"] = sil_app

    actual_context = generator.get_document_context()

    assert sil_expected_preview_context == actual_context


@patch.multiple(
    "web.utils.pdf.utils",
    _get_fa_sil_goods=MagicMock(
        return_value=[("goods one", 10), ("goods two", 20), ("goods three", 30)]
    ),
    _get_licence_number=MagicMock(return_value="0000001B"),
)
def test_get_fa_sil_licence_pre_sign_context(sil_app, licence, sil_expected_preview_context):
    generator = PdfGenerator(sil_app, licence, types.DocumentTypes.LICENCE_PRE_SIGN)

    sil_expected_preview_context["page_title"] = "Licence Preview"
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

    generator = PdfGenerator(app, licence, types.DocumentTypes.LICENCE_PREVIEW)

    expected_context = {
        "process": app,
        "page_title": "Licence Preview",
        "preview_licence": True,
        "paper_licence_only": False,
        "issue_date": datetime.date.today().strftime("%d %B %Y"),
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


# TODO: Remove the default tests when every app type has been implemented
def test_get_default_cover_letter_context(licence):
    app = DFLApplication(process_type=DFLApplication.PROCESS_TYPE)

    generator = PdfGenerator(app, licence, types.DocumentTypes.COVER_LETTER)

    expected_context = {
        "process": app,
        "page_title": "Cover Letter Preview",
        "preview_licence": False,
        "paper_licence_only": False,
        "issue_date": datetime.date.today().strftime("%d %B %Y"),
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "licence_start_date": "TODO: SET THIS VALUE",
        "licence_end_date": "TODO: SET THIS VALUE",
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
    generator = PdfGenerator(oil_app, licence, types.DocumentTypes.LICENCE_PREVIEW)
    pdf_file = generator.get_pdf()

    # This tests doesn't actually do a great deal other than check it creates
    # a pdf, however all the methods have already been tested.
    assert pdf_file.startswith(b"%PDF-")
