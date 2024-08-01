from web.tests.utils.pdf.test_visual_regression import BENCHMARK_PDF_DIRECTORY
from web.tests.utils.pdf.test_visual_regression.generate_benchmark_pdfs.utils import (
    update_timestamp,
)
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, StaticPdfGenerator


def _generate_certificate_benchmark_pdf(app, file_name):
    country = app.countries.first()
    certificate = app.certificates.first()

    certificate.case_completion_datetime = None
    certificate.save()

    generator = PdfGenerator(DocumentTypes.CERTIFICATE_SIGNED, app, certificate, country)
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)


class TestGenerateComLicenceBenchmarkPDF:
    def test_generate_benchmark_com_certificate(self, completed_com_app):
        _generate_certificate_benchmark_pdf(completed_com_app, "com_certificate.pdf")

    def test_generate_benchmark_com_long_certificate(self, pdf_long_com_app):
        _generate_certificate_benchmark_pdf(pdf_long_com_app, "com_long_certificate.pdf")


class TestGenerateGmpLicenceBenchmarkPDF:
    def test_generate_benchmark_gmp_certificate(self, completed_gmp_app):
        _generate_certificate_benchmark_pdf(completed_gmp_app, "gmp_certificate.pdf")


class TestGenerateCfsLicenceBenchmarkPDF:
    def test_generate_benchmark_cfs_certificate(self, completed_cfs_app):
        _generate_certificate_benchmark_pdf(completed_cfs_app, "cfs_certificate.pdf")

    def test_generate_benchmark_cfs_cover_letter(self):
        file_name = "cfs_cover_letter.pdf"

        generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
        (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
        update_timestamp(file_name)
