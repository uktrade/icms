"""These tests generate benchmark PDFs for visual regression testing.

They are not really tests and as such are not ran as part of the test suite. The reason they are written as tests is
that they depend on pytest fixtures to populate the data needed to produce the PDFs."""

from web.tests.utils.pdf.test_visual_regression import BENCHMARK_PDF_DIRECTORY
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, StaticPdfGenerator


def test_generate_benchmark_cfs_certificate(completed_cfs_app):
    country = completed_cfs_app.countries.first()
    certificate = completed_cfs_app.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_SIGNED, completed_cfs_app, certificate, country
    )
    (BENCHMARK_PDF_DIRECTORY / "cfs_certificate.pdf").write_bytes(generator.get_pdf())


def test_generate_benchmark_com_certificate(completed_com_app):
    country = completed_com_app.countries.first()
    certificate = completed_com_app.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_SIGNED, completed_com_app, certificate, country
    )
    (BENCHMARK_PDF_DIRECTORY / "com_certificate.pdf").write_bytes(generator.get_pdf())


def test_generate_benchmark_gmp_certificate(completed_gmp_app):
    country = completed_gmp_app.countries.first()
    certificate = completed_gmp_app.certificates.first()
    generator = PdfGenerator(
        DocumentTypes.CERTIFICATE_SIGNED, completed_gmp_app, certificate, country
    )
    (BENCHMARK_PDF_DIRECTORY / "gmp_certificate.pdf").write_bytes(generator.get_pdf())


def test_generate_oil_licence(completed_oil_app):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_SIGNED, completed_oil_app, completed_oil_app.licences.first()
    )
    (BENCHMARK_PDF_DIRECTORY / "oil_licence.pdf").write_bytes(generator.get_pdf())


def test_generate_dfl_licence(completed_dfl_app):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_SIGNED, completed_dfl_app, completed_dfl_app.licences.first()
    )
    (BENCHMARK_PDF_DIRECTORY / "dfl_licence.pdf").write_bytes(generator.get_pdf())


def test_generate_sil_licence(completed_sil_app):
    generator = PdfGenerator(
        DocumentTypes.LICENCE_SIGNED, completed_sil_app, completed_sil_app.licences.first()
    )
    (BENCHMARK_PDF_DIRECTORY / "sil_licence.pdf").write_bytes(generator.get_pdf())


def test_generate_cfs_cover_letter():
    generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
    (BENCHMARK_PDF_DIRECTORY / "cfs_cover_letter.pdf").write_bytes(generator.get_pdf())


def test_generate_cover_letter(completed_dfl_app):
    completed_dfl_app.cover_letter_text = "ABC"

    generator = PdfGenerator(
        DocumentTypes.COVER_LETTER_SIGNED,
        completed_dfl_app,
        completed_dfl_app.licences.first(),
    )
    (BENCHMARK_PDF_DIRECTORY / "cover_letter.pdf").write_bytes(generator.get_pdf())
