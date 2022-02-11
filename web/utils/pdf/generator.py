from dataclasses import dataclass
from typing import Any

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string

from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes
from web.types import AuthenticatedHttpRequest

from . import utils
from .types import DocumentTypes


@dataclass
class PdfGenerator:
    application: ImpOrExp
    doc_type: DocumentTypes
    request: AuthenticatedHttpRequest

    def get_pdf(self) -> bytes:
        html_string = self.get_document_html()
        base_url = self.request.build_absolute_uri()

        html = weasyprint.HTML(string=html_string, base_url=base_url)
        pdf_file = html.write_pdf()

        return pdf_file

    # TODO: Remove this when all the pdfs have been created
    def get_document_html(self) -> str:
        return render_to_string(
            request=self.request,
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

            # Default
            return "web/domains/case/import/manage/preview-licence.html"

        if self.doc_type == DocumentTypes.LICENCE_PRE_SIGN:
            if self.application.process_type == ProcessTypes.FA_OIL:
                return "pdf/import/fa-oil-licence-pre-sign.html"

            if self.application.process_type == ProcessTypes.FA_DFL:
                return "pdf/import/fa-dfl-licence-pre-sign.html"

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
            "paper_licence_only": self.application.issue_paper_licence_only or False,
        }

        # This will be extended to return the correct context for a given process & doc type
        if self.doc_type == DocumentTypes.COVER_LETTER:
            extra = {
                "page_title": "Cover Letter Preview",
                # TODO: licence_issue_date is a property and should probably be application.licence_start_date
                "issue_date": self.application.licence_issue_date.strftime("%d %B %Y"),
                "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
            }

        elif self.doc_type in [DocumentTypes.LICENCE_PREVIEW, DocumentTypes.LICENCE_PRE_SIGN]:
            if self.application.process_type == ProcessTypes.FA_OIL:
                extra = utils.get_fa_oil_licence_context(self.application, self.doc_type)

            elif self.application.process_type == ProcessTypes.FA_DFL:
                extra = utils.get_fa_dfl_licence_context(self.application, self.doc_type)

            else:
                extra = {
                    "page_title": "Licence Preview",
                    # TODO: licence_issue_date is a property and should probably be application.licence_start_date
                    "issue_date": self.application.licence_issue_date.strftime("%d %B %Y"),
                }
        else:
            raise ValueError(f"Unsupported document type: {self.doc_type}")

        return common_context | extra
