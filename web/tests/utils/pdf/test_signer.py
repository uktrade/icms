import base64
import datetime as dt
import io
import logging
from unittest.mock import patch

import pytest
from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings
from django.test import override_settings
from endesive.pdf import verify

from web.types import DocumentTypes
from web.utils.pdf.exceptions import SignatureTextNotFound
from web.utils.pdf.generator import PdfGenBase
from web.utils.pdf.signer import sign_pdf


def test_dummy_certificate_details():
    key_and_certificate = pkcs12.load_key_and_certificates(
        base64.b64decode(settings.P12_SIGNATURE_BASE_64),  # /PS-IGNORE
        password=settings.P12_SIGNATURE_PASSWORD.encode(),
        backend=backends.default_backend(),
    )

    x509_cert: x509.Certificate = key_and_certificate[1]
    assert (
        x509_cert.subject.rfc4514_string()
        == "1.2.840.113549.1.9.1=emailAddress,CN=commonName,OU=organizationUnitName,O=organizationName,L=localityName,ST=stateOrProvinceName,C=GB"
    )
    assert x509_cert.not_valid_after_utc == dt.datetime(
        2034, 9, 8, 13, 3, 13, tzinfo=dt.timezone.utc
    )
    assert x509_cert.not_valid_before_utc == dt.datetime(
        2024, 9, 10, 13, 3, 13, tzinfo=dt.timezone.utc
    )


@patch("web.utils.pdf.generator.PdfGenBase.get_document_html")
@pytest.fixture()
def dummy_pdf():
    """Generate a dummy pdf for testing"""
    with patch("web.utils.pdf.generator.PdfGenBase.get_document_html") as patched_get_document_html:
        target = io.BytesIO()
        patched_get_document_html.return_value = (
            "<html><p>Signed by Test Signatory</p><p>On behalf of the Secretary of State</p></html>"
        )
        PdfGenBase(doc_type=DocumentTypes.LICENCE_PREVIEW).get_pdf(target=target)
        return target


@override_settings(P12_SIGNATURE_BASE_64="")
def test_sign_pdf_no_key(caplog, dummy_pdf):
    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(dummy_pdf)

    assert "P12_SIGNATURE_BASE_64 environment variable not set for this environment." in caplog.text

    pdf.seek(0)
    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@pytest.mark.django_db
@override_settings(P12_SIGNATURE_PASSWORD="")
def test_sign_pdf_no_password(caplog, dummy_pdf):
    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(dummy_pdf)

    assert (
        "P12_SIGNATURE_PASSWORD environment variable not set for this environment." in caplog.text
    )

    pdf.seek(0)
    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@patch("web.utils.pdf.signer.get_active_signature_image")
def test_sign_pdf(
    mock_get_active_signature_image,
    dummy_signature_image,
    dummy_pdf,
):
    mock_get_active_signature_image.return_value = dummy_signature_image
    signed_pdf = sign_pdf(dummy_pdf)
    signed_pdf.seek(0)
    pdf_bytes = signed_pdf.getvalue()
    verification = verify(pdf_bytes)

    # The verification is a list of booleans, one for hash, signature, and certificate.
    # We don't care about the certificate as we don't pass it in, so we just check the other two.
    assert verification == [(True, True, False)]


@patch("web.utils.pdf.generator.PdfGenBase.get_document_html")
def test_no_signature_placeholder(mock_get_document_html):
    mock_get_document_html.return_value = "<html><p>Some text</p></html>"
    target = io.BytesIO()
    PdfGenBase(doc_type=DocumentTypes.LICENCE_PREVIEW).get_pdf(target=target)
    with pytest.raises(SignatureTextNotFound):
        sign_pdf(target)
