from web.tests.utils.pdf.test_visual_regression import BaseTestPDFVisualRegression
from web.types import DocumentTypes
from web.utils.pdf import StaticPdfGenerator


class BaseTestExportPDFVisualRegression(BaseTestPDFVisualRegression):
    def get_generator_kwargs(self):
        kwargs = super().get_generator_kwargs()
        kwargs["country"] = self.application.countries.first()
        kwargs["doc_type"] = DocumentTypes.CERTIFICATE_PREVIEW
        kwargs["doc_pack"] = self.application.certificates.first()
        return kwargs


class TestComCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file = "com_certificate.pdf"

    def test_pdf(self, com_app_submitted):
        self.application = com_app_submitted
        self.compare_pdf()


class TestCfsCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file = "cfs_certificate.pdf"

    def test_pdf(self, cfs_app_submitted):
        self.application = cfs_app_submitted
        self.compare_pdf()


class TestGmpCertificate(BaseTestExportPDFVisualRegression):
    benchmark_pdf_image_file = "gmp_certificate.pdf"

    def test_pdf(self, gmp_app_submitted):
        self.application = gmp_app_submitted
        self.compare_pdf()


class TestCfsCoverLetter(BaseTestPDFVisualRegression):
    benchmark_pdf_image_file = "cfs_cover_letter.pdf"

    def get_generator(self):
        return StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)

    def test_pdf(self):
        self.compare_pdf()
