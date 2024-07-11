from web.tests.utils.pdf.test_visual_regression import BaseTestPDFVisualRegression
from web.types import DocumentTypes
from web.utils.pdf import StaticPdfGenerator


class BaseTestExportPDFVisualRegression(BaseTestPDFVisualRegression):
    def get_generator_kwargs(self):
        kwargs = super().get_generator_kwargs()
        kwargs["country"] = self.application.countries.first()
        kwargs["doc_type"] = DocumentTypes.CERTIFICATE_SIGNED
        kwargs["doc_pack"] = self.application.certificates.first()
        return kwargs


class TestComCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file_path = "com_certificate.pdf"

    def test_pdf(self, completed_com_app):
        self.application = completed_com_app
        self.compare_pdf()


class TestCfsCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file_path = "cfs_certificate.pdf"

    def test_pdf(self, completed_cfs_app):
        self.application = completed_cfs_app
        self.compare_pdf()


class TestGmpCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file_path = "gmp_certificate.pdf"

    def test_pdf(self, completed_gmp_app):
        self.application = completed_gmp_app
        self.compare_pdf()


class TestCfsCoverLetter(BaseTestPDFVisualRegression):
    benchmark_pdf_image_file_path = "cfs_cover_letter.pdf"

    def get_generator(self):
        return StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)

    def test_pdf(self):
        self.compare_pdf()
