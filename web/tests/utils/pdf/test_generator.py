import datetime

import pytest
from django.conf import settings

from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.types import AuthenticatedHttpRequest
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
        # All other licence types use the default for LICENCE_PREVIEW
        (
            DFLApplication,
            types.DocumentTypes.LICENCE_PREVIEW,
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
def test_get_template(AppCls, doc_type, expected_template):
    request = AuthenticatedHttpRequest()
    app = AppCls(process_type=AppCls.PROCESS_TYPE)

    generator = PdfGenerator(app, doc_type, request)
    actual_template = generator.get_template()

    assert expected_template == actual_template


def test_get_template_raises_error_if_doc_type_unsupported():
    request = AuthenticatedHttpRequest()
    app = OpenIndividualLicenceApplication(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE
    )
    generator = PdfGenerator(app, "INVALID_DOC_TYPE", request)

    with pytest.raises(ValueError, match="Unsupported document type"):
        generator.get_template()


def test_get_fa_oil_preview_licence_context(oil_app, oil_expected_preview_context):
    request = AuthenticatedHttpRequest()
    generator = PdfGenerator(oil_app, types.DocumentTypes.LICENCE_PREVIEW, request)

    oil_expected_preview_context["page_title"] = "Licence Preview"
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["process"] = oil_app

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


def test_get_fa_oil_licence_pre_sign_context(oil_app, oil_expected_preview_context):
    request = AuthenticatedHttpRequest()
    generator = PdfGenerator(oil_app, types.DocumentTypes.LICENCE_PRE_SIGN, request)

    oil_expected_preview_context["page_title"] = "Licence Preview"
    oil_expected_preview_context["preview_licence"] = False
    oil_expected_preview_context["process"] = oil_app
    oil_expected_preview_context["licence_number"] = "ICMSLST-1224: Real Licence Number"

    actual_context = generator.get_document_context()

    assert oil_expected_preview_context == actual_context


# TODO: Remove the default tests when every app type has been implemented
def test_get_default_preview_licence_context():
    app = DFLApplication(
        process_type=DFLApplication.PROCESS_TYPE, issue_date=datetime.date(2022, 4, 21)
    )

    request = AuthenticatedHttpRequest()
    generator = PdfGenerator(app, types.DocumentTypes.LICENCE_PREVIEW, request)

    expected_context = {
        "process": app,
        "page_title": "Licence Preview",
        "preview_licence": True,
        "issue_date": "21 April 2022",
    }

    actual_context = generator.get_document_context()
    assert expected_context == actual_context


# TODO: Remove the default tests when every app type has been implemented
def test_get_default_cover_letter_context():
    app = DFLApplication(
        process_type=DFLApplication.PROCESS_TYPE, issue_date=datetime.date(2022, 4, 21)
    )

    request = AuthenticatedHttpRequest()
    generator = PdfGenerator(app, types.DocumentTypes.COVER_LETTER, request)

    expected_context = {
        "process": app,
        "page_title": "Cover Letter Preview",
        "preview_licence": False,
        "issue_date": "21 April 2022",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }

    actual_context = generator.get_document_context()

    assert expected_context == actual_context


def test_get_document_context_raises_error_if_doc_type_unsupported():
    request = AuthenticatedHttpRequest()
    app = OpenIndividualLicenceApplication(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE
    )

    with pytest.raises(ValueError, match="Unsupported document type"):
        generator = PdfGenerator(app, "INVALID_DOC_TYPE", request)
        generator.get_document_context()


def test_get_pdf(oil_app):
    request = AuthenticatedHttpRequest()
    request.build_absolute_uri = lambda: "localhost"

    generator = PdfGenerator(oil_app, types.DocumentTypes.LICENCE_PREVIEW, request)
    pdf_file = generator.get_pdf()

    # This tests doesn't actually do a great deal other than check it creates
    # a pdf, however all the methods have already been tested.
    assert pdf_file.startswith(b"%PDF-")
