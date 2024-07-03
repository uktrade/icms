"""These tests generate benchmark PDFs for visual regression testing.

They are not really tests and as such are not ran as part of the test suite. The reason they are tests is that they
depend on pytest fixtures to populate the data needed to produce the PDFs."""

import datetime as dt
import json

import pytest

from web.tests.utils.pdf.test_visual_regression import BENCHMARK_PDF_DIRECTORY
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, StaticPdfGenerator


@pytest.fixture(autouse=True, scope="session")
def save_timestamp():
    """Save the current timestamp to a file so that we can freeze time when generating the PDFs we are going to test.

    We run this at the end of the session so that we only save the timestamp once."""
    yield
    date_stamp = {"date_created": dt.datetime.now().isoformat()}
    with open(BENCHMARK_PDF_DIRECTORY / "date_created.json", "w") as f:
        json.dump(date_stamp, f)


def test_generate_benchmark_cfs_certificate(cfs_app_submitted):
    country = cfs_app_submitted.countries.first()
    certificate = cfs_app_submitted.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_PREVIEW, cfs_app_submitted, certificate, country
    )
    with open(BENCHMARK_PDF_DIRECTORY / "cfs_certificate.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_benchmark_com_certificate(com_app_submitted):
    country = com_app_submitted.countries.first()
    certificate = com_app_submitted.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_PREVIEW, com_app_submitted, certificate, country
    )
    with open(BENCHMARK_PDF_DIRECTORY / "com_certificate.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_benchmark_gmp_certificate(gmp_app_submitted):
    country = gmp_app_submitted.countries.first()
    certificate = gmp_app_submitted.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_PREVIEW, gmp_app_submitted, certificate, country
    )
    with open(BENCHMARK_PDF_DIRECTORY / "gmp_certificate.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_oil_licence(fa_oil_app_submitted):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_PREVIEW, fa_oil_app_submitted, fa_oil_app_submitted.licences.first()
    )
    with open(BENCHMARK_PDF_DIRECTORY / "oil_licence.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_dfl_licence(fa_dfl_app_submitted):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_PREVIEW, fa_dfl_app_submitted, fa_dfl_app_submitted.licences.first()
    )
    with open(BENCHMARK_PDF_DIRECTORY / "dfl_licence.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_sil_licence(fa_sil_app_submitted):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_PREVIEW, fa_sil_app_submitted, fa_sil_app_submitted.licences.first()
    )
    with open(BENCHMARK_PDF_DIRECTORY / "sil_licence.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_cfs_cover_letter():
    generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
    with open(BENCHMARK_PDF_DIRECTORY / "cfs_cover_letter.pdf", "wb") as f:
        f.write(generator.get_pdf())


def test_generate_cover_letter(fa_dfl_app_submitted):
    fa_dfl_app_submitted.cover_letter_text = "ABC"

    generator = PdfGenerator(
        DocumentTypes.COVER_LETTER_PREVIEW,
        fa_dfl_app_submitted,
        fa_dfl_app_submitted.licences.first(),
    )
    with open(BENCHMARK_PDF_DIRECTORY / "cover_letter.pdf", "wb") as f:
        f.write(generator.get_pdf())
