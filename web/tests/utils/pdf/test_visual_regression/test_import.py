from web.tests.utils.pdf.test_visual_regression import BaseTestPDFVisualRegression
from web.types import DocumentTypes


class BaseTestImportPDFVisualRegression(BaseTestPDFVisualRegression):
    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.LICENCE_SIGNED
        kwargs["doc_pack"] = self.application.licences.first()
        return kwargs


class TestOilLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file_path = "oil_licence.pdf"

    def test_pdf(self, completed_oil_app):
        self.application = completed_oil_app
        self.compare_pdf()


class TestDflLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file_path = "dfl_licence.pdf"

    def test_pdf(self, completed_dfl_app):
        self.application = completed_dfl_app
        self.compare_pdf()


class TestSilLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file_path = "sil_licence.pdf"

    def test_pdf(self, completed_sil_app):
        self.application = completed_sil_app
        self.compare_pdf()


class TestCoverLetter(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file_path = "cover_letter.pdf"

    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.COVER_LETTER_SIGNED
        return kwargs

    def test_pdf(self, completed_dfl_app):
        completed_dfl_app.cover_letter_text = "Hello\n" * 500
        self.application = completed_dfl_app
        self.compare_pdf()
