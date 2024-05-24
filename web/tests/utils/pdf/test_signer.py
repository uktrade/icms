import base64
import io
import logging
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from endesive.pdf import verify
from OpenSSL import crypto

from web.types import DocumentTypes
from web.utils.pdf.exceptions import SignatureTextNotFound
from web.utils.pdf.generator import PdfGenBase
from web.utils.pdf.signer import sign_pdf

MOCK_CERT_PASSWORD = "123456"


@pytest.fixture()
def pkc12_base64():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)
    cert = crypto.X509()
    cert.get_subject().C = "GB"
    cert.get_subject().ST = "stateOrProvinceName"
    cert.get_subject().L = "localityName"
    cert.get_subject().O = "organizationName"  # noqa: E741
    cert.get_subject().OU = "organizationUnitName"
    cert.get_subject().CN = "commonName"
    cert.get_subject().emailAddress = "emailAddress"
    cert.set_serial_number(0)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha512")

    p12 = crypto.PKCS12()
    p12.set_privatekey(key)
    p12.set_certificate(cert)
    p12_data = p12.export(passphrase=MOCK_CERT_PASSWORD.encode())

    return base64.b64encode(p12_data)  # /PS-IGNORE


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
@override_settings(P12_SIGNATURE_PASSWORD=MOCK_CERT_PASSWORD)
def test_sign_pdf_no_key(caplog, dummy_pdf):
    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(dummy_pdf)

    assert "P12_SIGNATURE_BASE_64 environment variable not set for this environment." in caplog.text

    pdf.seek(0)
    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@override_settings(P12_SIGNATURE_PASSWORD="")
def test_sign_pdf_no_password(caplog, pkc12_base64, dummy_pdf):
    settings.P12_SIGNATURE_BASE_64 = pkc12_base64

    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(dummy_pdf)

    assert (
        "P12_SIGNATURE_PASSWORD environment variable not set for this environment." in caplog.text
    )

    pdf.seek(0)
    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@override_settings(P12_SIGNATURE_PASSWORD=MOCK_CERT_PASSWORD)
@patch("web.utils.pdf.signer.get_active_signature_image")
def test_sign_pdf(
    mock_get_active_signature_image,
    pkc12_base64,
    dummy_signature_image,
    dummy_pdf,
):
    mock_get_active_signature_image.return_value = dummy_signature_image
    settings.P12_SIGNATURE_BASE_64 = pkc12_base64
    signed_pdf = sign_pdf(dummy_pdf)
    signed_pdf.seek(0)
    pdf_bytes = signed_pdf.getvalue()
    verification = verify(pdf_bytes)

    # The verification is a list of booleans, one for hash, signature, and certificate.
    # We don't care about the certificate as we don't pass it in, so we just check the other two.
    assert verification == [(True, True, False)]


@override_settings(P12_SIGNATURE_PASSWORD=MOCK_CERT_PASSWORD)
@patch("web.utils.pdf.generator.PdfGenBase.get_document_html")
def test_no_signature_placeholder(mock_get_document_html, pkc12_base64):
    settings.P12_SIGNATURE_BASE_64 = pkc12_base64
    mock_get_document_html.return_value = "<html><p>Some text</p></html>"
    target = io.BytesIO()
    PdfGenBase(doc_type=DocumentTypes.LICENCE_PREVIEW).get_pdf(target=target)
    with pytest.raises(SignatureTextNotFound):
        sign_pdf(target)
