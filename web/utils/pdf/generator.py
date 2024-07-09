import io
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright

from web.domains.case.types import DocumentPack, ImpOrExp
from web.flow.models import ProcessTypes
from web.models import Country
from web.types import DocumentTypes

from . import pages, utils


@dataclass
class PdfGenBase:
    doc_type: DocumentTypes

    def get_pdf(self, target: io.BytesIO | None = None) -> bytes | None:
        """Write the pdf data to the optional target or return the PDF as bytes

        :param target: Optional target to write to
        :return: None if target is supplied else bytes
        """
        document_html = self.get_document_html()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.set_content(document_html)

            pdf_data = page.pdf(format="A4")

        pdf_data = self.format_pages(pdf_data)

        if target:
            target.write(pdf_data)
            return None

        return pdf_data

    def get_document_html(self) -> str:
        return render_to_string(
            template_name=self.get_template(),
            context=self.get_document_context(),
        )

    def format_pages(self, pdf_data: bytes) -> bytes:
        return pdf_data

    def get_template(self) -> str:
        """Returns the correct template"""
        raise ValueError(f"Unsupported document type: {self.doc_type}")

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""
        raise ValueError(f"Unsupported document type: {self.doc_type}")


@dataclass
class PdfGenerator(PdfGenBase):
    application: ImpOrExp
    doc_pack: DocumentPack
    country: Country | None = None

    def get_template(self) -> str:
        """Returns the correct template"""

        if self.doc_type in [
            DocumentTypes.COVER_LETTER_PREVIEW,
            DocumentTypes.COVER_LETTER_PRE_SIGN,
            DocumentTypes.COVER_LETTER_SIGNED,
        ]:
            return "pdf/import/cover-letter.html"
        else:
            match self.application.process_type:
                case ProcessTypes.FA_OIL:
                    return "pdf/import/fa-oil-licence.html"
                case ProcessTypes.FA_DFL:
                    return "pdf/import/fa-dfl-licence.html"
                case ProcessTypes.FA_SIL:
                    return "pdf/import/fa-sil-licence.html"
                case ProcessTypes.SANCTIONS:
                    return "pdf/import/sanctions-licence.html"
                case ProcessTypes.WOOD:
                    return "pdf/import/wood-licence.html"
                case ProcessTypes.CFS:
                    return "pdf/export/cfs-certificate.html"
                case ProcessTypes.COM:
                    return "pdf/export/com-certificate.html"
                case ProcessTypes.GMP:
                    return "pdf/export/gmp-certificate.html"
                case _:
                    raise ValueError(f"Unsupported process type: {self.application.process_type}")

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""

        if self.doc_type in [
            DocumentTypes.COVER_LETTER_PREVIEW,
            DocumentTypes.COVER_LETTER_PRE_SIGN,
            DocumentTypes.COVER_LETTER_SIGNED,
        ]:
            return utils.get_cover_letter_context(self.application, self.doc_type)

        if (
            self.application.process_type
            in [
                ProcessTypes.CFS,
                ProcessTypes.COM,
                ProcessTypes.GMP,
            ]
            and not self.country
        ):
            raise ValueError("Country must be specified for export certificates")

        match self.application.process_type:
            case ProcessTypes.FA_OIL:
                context = utils.get_fa_oil_licence_context(
                    self.application, self.doc_pack, self.doc_type
                )
            case ProcessTypes.FA_DFL:
                context = utils.get_fa_dfl_licence_context(
                    self.application, self.doc_pack, self.doc_type
                )
            case ProcessTypes.FA_SIL:
                context = utils.get_fa_sil_licence_context(
                    self.application, self.doc_pack, self.doc_type
                )
            case ProcessTypes.SANCTIONS:
                context = utils.get_sanctions_licence_context(
                    self.application, self.doc_pack, self.doc_type
                )
            case ProcessTypes.WOOD:
                context = utils.get_wood_licence_context(
                    self.application, self.doc_pack, self.doc_type
                )
            case ProcessTypes.CFS:
                context = utils.get_cfs_certificate_context(
                    self.application,
                    self.doc_pack,
                    self.doc_type,
                    self.country,  # type:ignore[arg-type]
                )
            case ProcessTypes.COM:
                context = utils.get_com_certificate_context(
                    self.application,
                    self.doc_pack,
                    self.doc_type,
                    self.country,  # type:ignore[arg-type]
                )
            case ProcessTypes.GMP:
                context = utils.get_gmp_certificate_context(
                    self.application,
                    self.doc_pack,
                    self.doc_type,
                    self.country,  # type:ignore[arg-type]
                )
            case _:
                raise ValueError(f"Unsupported process type: {self.application.process_type}")

        return context

    def format_pages(self, pdf_data: bytes) -> bytes:
        match self.application.process_type:
            case ProcessTypes.CFS:
                return pages.format_cfs_pages(pdf_data, self.get_document_context())
            case ProcessTypes.COM:
                return pages.format_com_pages(pdf_data)
            case _:
                return pdf_data


@dataclass
class StaticPdfGenerator(PdfGenBase):
    def get_template(self) -> str:
        """Returns the correct template"""
        if self.doc_type == DocumentTypes.CFS_COVER_LETTER:
            return "pdf/export/cfs-letter.html"

        return super().get_template()

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""

        if self.doc_type == DocumentTypes.CFS_COVER_LETTER:
            return {
                "ilb_contact_address_split": settings.ILB_CONTACT_ADDRESS.split(", "),
                "ilb_contact_name": settings.ILB_CONTACT_NAME,
                "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
            }

        return super().get_document_context()
