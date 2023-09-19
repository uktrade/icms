import io
from dataclasses import dataclass
from typing import Any

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string

from web.domains.case.types import DocumentPack, ImpOrExp
from web.flow.models import ProcessTypes
from web.models import Country
from web.types import DocumentTypes

from . import utils


@dataclass
class PdfGenerator:
    application: ImpOrExp
    doc_pack: DocumentPack
    doc_type: DocumentTypes
    country: Country | None = None

    def get_pdf(self, target: io.BytesIO | None = None) -> bytes | None:
        """Write the pdf data to the optional target or return the PDF as bytes

        :param target: Optional target to write to
        :return: None if target is supplied else bytes
        """

        html_string = self.get_document_html()
        html = weasyprint.HTML(string=html_string, base_url=settings.PDF_DEFAULT_DOMAIN)

        return html.write_pdf(target=target)

    # TODO: Remove this when all the pdfs have been created
    # See web/domains/case/views/views_pdf.py for example
    def get_document_html(self) -> str:
        return render_to_string(
            template_name=self.get_template(),
            context=self.get_document_context(),
        )

    def get_template(self) -> str:
        """Returns the correct template"""

        if self.doc_type in [
            DocumentTypes.COVER_LETTER_PREVIEW,
            DocumentTypes.COVER_LETTER_PRE_SIGN,
            DocumentTypes.COVER_LETTER_SIGNED,
        ]:
            # TODO ICMSLST-697 Revisit when signing the - document may need different templates
            return "pdf/import/cover-letter.html"

        if self.doc_type == DocumentTypes.LICENCE_PREVIEW:
            match self.application.process_type:
                case ProcessTypes.FA_OIL:
                    return "pdf/import/fa-oil-licence-preview.html"
                case ProcessTypes.FA_DFL:
                    return "pdf/import/fa-dfl-licence-preview.html"
                case ProcessTypes.FA_SIL:
                    return "pdf/import/fa-sil-licence-preview.html"
                case _:
                    return "web/domains/case/import/manage/preview-licence.html"

        # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
        if self.doc_type in (DocumentTypes.LICENCE_PRE_SIGN, DocumentTypes.LICENCE_SIGNED):
            match self.application.process_type:
                case ProcessTypes.FA_OIL:
                    return "pdf/import/fa-oil-licence-pre-sign.html"
                case ProcessTypes.FA_DFL:
                    return "pdf/import/fa-dfl-licence-pre-sign.html"
                case ProcessTypes.FA_SIL:
                    return "pdf/import/fa-sil-licence-pre-sign.html"
                case _:
                    return "web/domains/case/import/manage/preview-licence.html"

        if self.doc_type in (
            DocumentTypes.CERTIFICATE_PREVIEW,
            DocumentTypes.CERTIFICATE_PRE_SIGN,
            DocumentTypes.CERTIFICATE_SIGNED,
        ):
            match self.application.process_type:
                case ProcessTypes.CFS:
                    return "pdf/export/cfs-certificate.html"
                case ProcessTypes.COM:
                    return "pdf/export/com-certificate.html"
                case ProcessTypes.GMP:
                    return "pdf/export/gmp-certificate.html"
                case _:
                    raise ValueError(f"Unsupported process type: {self.application.process_type}")

        raise ValueError(f"Unsupported document type: {self.doc_type}")

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""

        # This will be extended to return the correct context for a given process & doc type
        if self.doc_type in [
            DocumentTypes.COVER_LETTER_PREVIEW,
            DocumentTypes.COVER_LETTER_PRE_SIGN,
            DocumentTypes.COVER_LETTER_SIGNED,
        ]:
            return utils.get_cover_letter_context(self.application, self.doc_type)

        # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
        elif self.doc_type in [
            DocumentTypes.LICENCE_PREVIEW,
            DocumentTypes.LICENCE_PRE_SIGN,
            DocumentTypes.LICENCE_SIGNED,
        ]:
            match self.application.process_type:
                case ProcessTypes.FA_OIL:
                    return utils.get_fa_oil_licence_context(
                        self.application, self.doc_pack, self.doc_type
                    )
                case ProcessTypes.FA_DFL:
                    return utils.get_fa_dfl_licence_context(
                        self.application, self.doc_pack, self.doc_type
                    )
                case ProcessTypes.FA_SIL:
                    return utils.get_fa_sil_licence_context(
                        self.application, self.doc_pack, self.doc_type
                    )
                case _:
                    return utils.get_licence_context(self.application, self.doc_pack, self.doc_type)

        elif self.doc_type in [
            DocumentTypes.CERTIFICATE_PREVIEW,
            DocumentTypes.CERTIFICATE_PRE_SIGN,
            DocumentTypes.CERTIFICATE_SIGNED,
        ]:
            if not self.country:
                raise ValueError("Country must be specified for export certificates")

            match self.application.process_type:
                case ProcessTypes.CFS:
                    return utils.get_cfs_certificate_context(
                        self.application, self.doc_pack, self.doc_type, self.country
                    )
                case ProcessTypes.COM:
                    return utils.get_com_certificate_context(
                        self.application, self.doc_pack, self.doc_type, self.country
                    )
                case ProcessTypes.GMP:
                    return utils.get_gmp_certificate_context(
                        self.application, self.doc_pack, self.doc_type, self.country
                    )
                case _:
                    raise ValueError(f"Unsupported process type: {self.application.process_type}")
        else:
            raise ValueError(f"Unsupported document type: {self.doc_type}")
