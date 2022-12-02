import io
from dataclasses import dataclass
from typing import Any

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from web.domains.case._import.models import ImportApplicationLicence
from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes

from . import utils
from .types import DocumentTypes


@dataclass
class PdfGenerator:
    application: ImpOrExp
    licence: ImportApplicationLicence
    doc_type: DocumentTypes

    def get_pdf(self, target: io.BytesIO | None = None) -> bytes | None:
        """Write the pdf data to the optional target or return the PDF as bytes

        :param target: Optional target to write to
        :return: None if target is supplied else bytes
        """

        html_string = self.get_document_html()
        html = weasyprint.HTML(string=html_string, base_url=settings.PDF_DEFAULT_DOMAIN)

        return html.write_pdf(target=target)

    # TODO: Remove this when all the pdfs have been created
    # See icms/web/domains/case/views/views_pdf.py for example
    def get_document_html(self) -> str:
        return render_to_string(
            template_name=self.get_template(),
            context=self.get_document_context(),
        )

    def get_template(self) -> str:
        """Returns the correct template"""

        # we only have two hardcoded templates currently
        # This will be extended to return the correct template for a given process & doc type
        if self.doc_type == DocumentTypes.COVER_LETTER:
            return "web/domains/case/import/manage/preview-cover-letter.html"

        if self.doc_type == DocumentTypes.LICENCE_PREVIEW:
            if self.application.process_type == ProcessTypes.FA_OIL:
                return "pdf/import/fa-oil-licence-preview.html"
            if self.application.process_type == ProcessTypes.FA_DFL:
                return "pdf/import/fa-dfl-licence-preview.html"
            if self.application.process_type == ProcessTypes.FA_SIL:
                return "pdf/import/fa-sil-licence-preview.html"

            # Default
            return "web/domains/case/import/manage/preview-licence.html"

        # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
        if self.doc_type in (DocumentTypes.LICENCE_PRE_SIGN, DocumentTypes.LICENCE_SIGNED):
            if self.application.process_type == ProcessTypes.FA_OIL:
                return "pdf/import/fa-oil-licence-pre-sign.html"

            if self.application.process_type == ProcessTypes.FA_DFL:
                return "pdf/import/fa-dfl-licence-pre-sign.html"

            if self.application.process_type == ProcessTypes.FA_SIL:
                return "pdf/import/fa-sil-licence-pre-sign.html"

            # Default
            return "web/domains/case/import/manage/preview-licence.html"

        raise ValueError(f"Unsupported document type: {self.doc_type}")

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""

        # TODO: Split this out when doing cover letters.
        common_context: dict[str, Any] = {
            "process": self.application,  # TODO: Remove when default has been deleted
            "page_title": "Licence Preview",
            "preview_licence": self.doc_type == DocumentTypes.LICENCE_PREVIEW,
            "paper_licence_only": self.licence.issue_paper_licence_only or False,
        }

        # This will be extended to return the correct context for a given process & doc type
        if self.doc_type == DocumentTypes.COVER_LETTER:
            extra = {
                "page_title": "Cover Letter Preview",
                "issue_date": timezone.now().date().strftime("%d %B %Y"),
                "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
                "licence_start_date": "TODO: SET THIS VALUE",
                "licence_end_date": "TODO: SET THIS VALUE",
            }

        # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
        elif self.doc_type in [
            DocumentTypes.LICENCE_PREVIEW,
            DocumentTypes.LICENCE_PRE_SIGN,
            DocumentTypes.LICENCE_SIGNED,
        ]:
            if self.application.process_type == ProcessTypes.FA_OIL:
                extra = utils.get_fa_oil_licence_context(
                    self.application, self.licence, self.doc_type
                )

            elif self.application.process_type == ProcessTypes.FA_DFL:
                extra = utils.get_fa_dfl_licence_context(
                    self.application, self.licence, self.doc_type
                )

            elif self.application.process_type == ProcessTypes.FA_SIL:
                extra = utils.get_fa_sil_licence_context(
                    self.application, self.licence, self.doc_type
                )

            else:
                extra = {
                    "page_title": "Licence Preview",
                    "issue_date": timezone.now().date().strftime("%d %B %Y"),
                }
        else:
            raise ValueError(f"Unsupported document type: {self.doc_type}")

        return common_context | extra
