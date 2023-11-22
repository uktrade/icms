import base64
import io
import logging

import pytest
import weasyprint
from django.conf import settings
from django.test import override_settings
from OpenSSL import crypto

from web.utils.pdf.signer import sign_pdf


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
    p12_data = p12.export()

    return base64.b64encode(p12_data)  # /PS-IGNORE


@override_settings(DIGITAL_SIGN_FLAG=False)
@override_settings(SIGNING_CERTIFICATE_PKCS12="")
def test_sign_pdf_no_dig_sign(caplog):
    target = io.BytesIO()
    html = weasyprint.HTML(string="<html></html>")
    html.write_pdf(target=target)

    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(target)

    assert "DIGITAL_SIGN_FLAG set to False for this environment." in caplog.text

    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@override_settings(DIGITAL_SIGN_FLAG=True)
@override_settings(SIGNING_CERTIFICATE_PKCS12="")
def test_sign_pdf_no_key(caplog):
    target = io.BytesIO()
    html = weasyprint.HTML(string="<html></html>")
    html.write_pdf(target=target)

    with caplog.at_level(logging.INFO):
        pdf = sign_pdf(target)

    assert "SIGNING_CERTIFICATE_PKS12 not set for this environment." in caplog.text

    pdf_bytes = pdf.getvalue()
    assert b"ByteRange" not in pdf_bytes
    assert b"Type /Sig" not in pdf_bytes


@override_settings(DIGITAL_SIGN_FLAG=True)
@override_settings(SIGNING_CERTIFICATE_PKCS12="")
def test_sign_pdf(pkc12_base64):
    settings.SIGNING_CERTIFICATE_PKCS12 = pkc12_base64
    target = io.BytesIO()
    html = weasyprint.HTML(string="<html></html>")
    html.write_pdf(target=target)
    pdf = sign_pdf(target)
    pdf_bytes = pdf.getvalue()

    assert b"ByteRange [ 00000000 00001240 00009344 00000556 ]" in pdf_bytes
    assert b"Type /Sig" in pdf_bytes
    assert b"/Filter /Adobe.PPKLite" in pdf_bytes
    assert b"/SubFilter /adbe.pkcs7.detached" in pdf_bytes
    assert b"Location (Department for Business and Trade)" in pdf_bytes
    assert b"Reason (On behalf of the Secretary of State)" in pdf_bytes
