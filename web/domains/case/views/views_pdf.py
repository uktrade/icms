from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.generic import View

from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import check_application_permission
from web.types import AuthenticatedHttpRequest
from web.utils.pdf import DocumentTypes, PdfGenerator

from .mixins import ApplicationTaskMixin


class PreviewLicenceBase(ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View):
    # ApplicationTaskMixin Config
    current_status = [
        ImpExpStatus.SUBMITTED,
        ImpExpStatus.PROCESSING,
        ImpExpStatus.VARIATION_REQUESTED,
    ]

    # View Config
    http_method_names = ["get"]

    def has_permission(self):
        self.set_application_and_task()

        try:
            check_application_permission(
                self.application, self.request.user, self.kwargs["case_type"]
            )
        except PermissionDenied:
            return False

        return True


class PreviewLicenceView(PreviewLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        pdf_gen = PdfGenerator(
            application=self.application,
            doc_type=DocumentTypes.LICENCE_PREVIEW,
            request=self.request,
        )

        return return_pdf(pdf_gen, "Licence.pdf")


class PreviewCoverLetterView(PreviewLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        pdf_gen = PdfGenerator(
            application=self.application, doc_type=DocumentTypes.COVER_LETTER, request=self.request
        )

        return return_pdf(pdf_gen, "CoverLetter.pdf")


def return_pdf(pdf_gen: PdfGenerator, filename: str) -> HttpResponse:
    pdf = pdf_gen.get_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"filename={filename}"

    return response
