from web.tests.utils.pdf.test_visual_regression import BENCHMARK_PDF_DIRECTORY
from web.tests.utils.pdf.test_visual_regression.generate_benchmark_pdfs.utils import (
    update_timestamp,
)
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator


def _generate_licence_benchmark_pdf(app, file_name):
    generator = PdfGenerator(DocumentTypes.LICENCE_SIGNED, app, app.licences.first())
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)


class TestGenerateOilLicenceBenchmarkPDF:
    def test_generate_benchmark_oil_licence(self, completed_oil_app):
        _generate_licence_benchmark_pdf(completed_oil_app, "oil_licence.pdf")

    def test_generate_benchmark_oil_long_licence(self, pdf_long_oil_app):
        _generate_licence_benchmark_pdf(pdf_long_oil_app, "oil_long_licence.pdf")

    def test_generate_benchmark_oil_paper_licence_only(self, pdf_paper_licence_only_oil_app):
        _generate_licence_benchmark_pdf(
            pdf_paper_licence_only_oil_app, "oil_paper_licence_only.pdf"
        )


class TestGenerateSilLicenceBenchmarkPDF:
    def test_generate_benchmark_sil_licence(self, completed_sil_app):
        _generate_licence_benchmark_pdf(completed_sil_app, "sil_licence.pdf")

    def test_generate_benchmark_sil_long_licence(self, pdf_long_sil_app):
        _generate_licence_benchmark_pdf(pdf_long_sil_app, "sil_long_licence.pdf")

    def test_generate_benchmark_sil_paper_licence_only(self, pdf_paper_licence_only_sil_app):
        _generate_licence_benchmark_pdf(
            pdf_paper_licence_only_sil_app, "sil_paper_licence_only.pdf"
        )


class TestGenerateDflLicenceBenchmarkPDF:
    def test_generate_benchmark_dfl_licence(self, completed_dfl_app):
        _generate_licence_benchmark_pdf(completed_dfl_app, "dfl_licence.pdf")

    def test_generate_benchmark_dfl_long_licence(self, pdf_long_dfl_app):
        _generate_licence_benchmark_pdf(pdf_long_dfl_app, "dfl_long_licence.pdf")

    def test_generate_benchmark_dfl_paper_licence_only(self, pdf_paper_licence_only_dfl_app):
        _generate_licence_benchmark_pdf(
            pdf_paper_licence_only_dfl_app, "dfl_paper_licence_only.pdf"
        )


class TestGenerateSanctionsLicenceBenchmarkPDF:
    def test_generate_benchmark_sanctions_licence(self, completed_sanctions_app):
        _generate_licence_benchmark_pdf(completed_sanctions_app, "sanctions_licence.pdf")


class TestGenerateCoverLetterBenchmarkPDF:
    @staticmethod
    def _generate_cover_letter_benchmark_pdf(app, file_name) -> None:
        generator = PdfGenerator(DocumentTypes.COVER_LETTER_SIGNED, app, app.licences.first())
        (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
        update_timestamp(file_name)

    def test_generate_benchmark_cover_letter(self, pdf_dfl_cover_letter_app):
        file_name = "cover_letter.pdf"
        self._generate_cover_letter_benchmark_pdf(pdf_dfl_cover_letter_app, file_name)

    def test_generate_benchmark_dfl_long_cover_letter(self, pdf_long_dfl_cover_letter_app):
        file_name = "dfl_long_cover_letter.pdf"
        self._generate_cover_letter_benchmark_pdf(pdf_long_dfl_cover_letter_app, file_name)
