from web.tests.utils.pdf.test_visual_regression import BaseTestPDFVisualRegression
from web.types import DocumentTypes


class BaseTestImportPDFVisualRegression(BaseTestPDFVisualRegression):
    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.LICENCE_SIGNED
        kwargs["doc_pack"] = self.application.licences.first()
        return kwargs


class TestOilLicence(BaseTestImportPDFVisualRegression):

    def test_pdf(self, completed_oil_app):
        self.benchmark_pdf_image_file_path = "oil_licence.pdf"
        self.application = completed_oil_app
        self.compare_pdf()

    def test_pdf_long(self, pdf_long_oil_app):
        self.benchmark_pdf_image_file_path = "oil_long_licence.pdf"
        self.application = pdf_long_oil_app
        self.compare_pdf()

    def test_pdf_paper_licence_only(self, pdf_paper_licence_only_oil_app):
        self.benchmark_pdf_image_file_path = "oil_paper_licence_only.pdf"
        self.application = pdf_paper_licence_only_oil_app
        self.compare_pdf()


class TestDflLicence(BaseTestImportPDFVisualRegression):

    def test_pdf(self, completed_dfl_app):
        self.benchmark_pdf_image_file_path = "dfl_licence.pdf"
        self.application = completed_dfl_app
        self.compare_pdf()

    def test_pdf_long(self, pdf_long_dfl_app):
        self.benchmark_pdf_image_file_path = "dfl_long_licence.pdf"
        self.application = pdf_long_dfl_app
        self.compare_pdf()

    def test_pdf_paper_licence_only(self, pdf_paper_licence_only_dfl_app):
        self.benchmark_pdf_image_file_path = "dfl_paper_licence_only.pdf"
        self.application = pdf_paper_licence_only_dfl_app
        self.compare_pdf()


class TestSilLicence(BaseTestImportPDFVisualRegression):

    def test_pdf(self, completed_sil_app):
        self.benchmark_pdf_image_file_path = "sil_licence.pdf"
        self.application = completed_sil_app
        self.compare_pdf()

    def test_pdf_long(self, pdf_long_sil_app):
        self.benchmark_pdf_image_file_path = "sil_long_licence.pdf"
        self.application = pdf_long_sil_app
        self.compare_pdf()

    def test_pdf_paper_licence_only(self, pdf_paper_licence_only_sil_app):
        self.benchmark_pdf_image_file_path = "sil_paper_licence_only.pdf"
        self.application = pdf_paper_licence_only_sil_app
        self.compare_pdf()


class TestCoverLetter(BaseTestImportPDFVisualRegression):

    def get_generator_kwargs(self) -> dict[str, any]:
        kwargs = super().get_generator_kwargs()
        kwargs["doc_type"] = DocumentTypes.COVER_LETTER_SIGNED
        return kwargs

    def test_pdf(self, pdf_dfl_cover_letter_app):
        self.benchmark_pdf_image_file_path = "cover_letter.pdf"
        self.application = pdf_dfl_cover_letter_app
        self.compare_pdf()

    def test_pdf_long(self, pdf_long_dfl_cover_letter_app):
        self.benchmark_pdf_image_file_path = "dfl_long_cover_letter.pdf"
        self.application = pdf_long_dfl_cover_letter_app
        self.compare_pdf()


class TestSanctionsLicence(BaseTestImportPDFVisualRegression):

    def test_pdf(self, completed_sanctions_app):
        self.benchmark_pdf_image_file_path = "sanctions_licence.pdf"
        self.application = completed_sanctions_app
        self.compare_pdf()
