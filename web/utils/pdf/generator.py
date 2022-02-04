from dataclasses import dataclass
from typing import Any

import weasyprint
from django.conf import settings
from django.template.loader import render_to_string

from web.domains.case.types import ImpOrExp
from web.types import AuthenticatedHttpRequest

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
            return "web/domains/case/import/manage/preview-licence.html"

        raise ValueError(f"Unsupported document type: {self.doc_type}")

    def get_document_context(self) -> dict[str, Any]:
        """Return the document context"""

        common_context: dict[str, Any] = {}
        extra: dict[str, Any] = {}

        # This will be extended to return the correct context for a given process & doc type
        if self.doc_type == DocumentTypes.COVER_LETTER:
            extra = {
                "process": self.application,
                "page_title": "Cover Letter Preview",
                # TODO: licence_issue_date is a property and should probably be application.licence_start_date
                "issue_date": self.application.licence_issue_date.strftime("%d %B %Y"),
                "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
            }

        elif self.doc_type == DocumentTypes.LICENCE_PREVIEW:
            extra = {
                "process": self.application,
                "page_title": "Licence Preview",
                # TODO: licence_issue_date is a property and should probably be application.licence_start_date
                "issue_date": self.application.licence_issue_date.strftime("%d %B %Y"),
            }

        return common_context | extra
