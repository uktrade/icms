from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.generic import View

from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import check_application_permission
from web.types import AuthenticatedHttpRequest
from web.utils.pdf import DocumentTypes, PdfGenerator

from .mixins import ApplicationTaskMixin


class GenerateLicenceBase(ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View):
    # ApplicationTaskMixin Config
    current_status = [
        ImpExpStatus.SUBMITTED,
        ImpExpStatus.PROCESSING,
        ImpExpStatus.VARIATION_REQUESTED,
    ]

    # View Config
    http_method_names = ["get"]

    # TODO: ICMSLST-1436 Add document_type permission checks.
    # e.g. document_type == "pre-sign" check the app has been "authorised"
    def has_permission(self):
        self.set_application_and_task()

        try:
            check_application_permission(
                self.application, self.request.user, self.kwargs["case_type"]
            )
        except PermissionDenied:
            return False

        return True


class PreviewLicenceView(GenerateLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        document_type = self.kwargs["document_type"]

        if document_type not in [DocumentTypes.LICENCE_PREVIEW, DocumentTypes.LICENCE_PRE_SIGN]:
            raise ValueError(f"Unable to preview document_type: {document_type}")

        pdf_gen = PdfGenerator(
            application=self.application,
            licence=self.application.get_most_recent_licence(),
            doc_type=document_type,
            request=self.request,
        )

        # TODO: Remove this when all the pdfs have been created
        # Useful when debugging pdf layout
        if "html" in self.request.GET:
            html = pdf_gen.get_document_html()
            return HttpResponse(html)

        return return_pdf(pdf_gen, "Licence-Preview.pdf")


class PreviewCoverLetterView(GenerateLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        pdf_gen = PdfGenerator(
            application=self.application,
            licence=self.application.get_most_recent_licence(),
            doc_type=DocumentTypes.COVER_LETTER,
            request=self.request,
        )

        return return_pdf(pdf_gen, "CoverLetter.pdf")


def return_pdf(pdf_gen: PdfGenerator, filename: str) -> HttpResponse:
    pdf = pdf_gen.get_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"filename={filename}"

    return response
