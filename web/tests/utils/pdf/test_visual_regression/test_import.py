from web.tests.utils.pdf.test_visual_regression import BaseTestPDFVisualRegression
from web.types import DocumentTypes


class BaseTestImportPDFVisualRegression(BaseTestPDFVisualRegression):
    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.LICENCE_PREVIEW
        kwargs["doc_pack"] = self.application.licences.first()
        return kwargs


class TestOilLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file = "oil_licence.pdf"

    def test_pdf(self, fa_oil_app_submitted):
        self.application = fa_oil_app_submitted
        self.compare_pdf()


class TestDflLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file = "dfl_licence.pdf"

    def test_pdf(self, fa_dfl_app_submitted):
        self.application = fa_dfl_app_submitted
        self.compare_pdf()


class TestSilLicence(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file = "sil_licence.pdf"

    def test_pdf(self, fa_sil_app_submitted):
        self.application = fa_sil_app_submitted
        self.compare_pdf()


class TestCoverLetter(BaseTestImportPDFVisualRegression):
    benchmark_pdf_image_file = "cover_letter.pdf"

    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.COVER_LETTER_PREVIEW
        return kwargs

    def test_pdf(self, fa_dfl_app_submitted):
        fa_dfl_app_submitted.cover_letter_text = "ABC"
        self.application = fa_dfl_app_submitted
        self.compare_pdf()
