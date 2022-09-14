from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.views.generic import View

from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import view_application_file
from web.domains.file.models import File
from web.flow.models import Process
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
    permission_required = ["web.ilb_admin"]


class PreviewLicenceView(GenerateLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        self.set_application_and_task()

        document_type = self.kwargs["document_type"]

        if document_type not in [DocumentTypes.LICENCE_PREVIEW, DocumentTypes.LICENCE_PRE_SIGN]:
            raise ValueError(f"Unable to preview document_type: {document_type}")

        pdf_gen = PdfGenerator(
            application=self.application,
            licence=self.application.get_latest_issued_document(),
            doc_type=document_type,
        )

        # TODO: Remove this when all the pdfs have been created
        # Useful when debugging pdf layout
        if "html" in self.request.GET:
            html = pdf_gen.get_document_html()
            return HttpResponse(html)

        return return_pdf(pdf_gen, "Licence-Preview.pdf")


class PreviewCoverLetterView(GenerateLicenceBase):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        self.set_application_and_task()

        pdf_gen = PdfGenerator(
            application=self.application,
            licence=self.application.get_latest_issued_document(),
            doc_type=DocumentTypes.COVER_LETTER,
        )

        return return_pdf(pdf_gen, "CoverLetter.pdf")


def return_pdf(pdf_gen: PdfGenerator, filename: str) -> HttpResponse:
    pdf = pdf_gen.get_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"filename={filename}"

    return response


@require_GET
@login_required
def view_case_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_type: str,
    object_pk: int,
    casedocumentreference_pk: int,
) -> HttpResponse:
    """Return a case document pdf.

    :param request: Django request object
    :param application_pk: Application pk
    :param case_type: "import" or "export"
    :param object_pk: ImportApplicationLicence or ExportApplicationCertificate pk
    :param casedocumentreference_pk: CaseDocumentReference pk
    :return: Case document pdf
    """

    # Application permission is checked in "view_application_file"
    application: ImpOrExp = get_object_or_404(Process, pk=application_pk).get_specific_model()

    obj = get_object_or_404(
        application.licences if application.is_import_application() else application.certificates,
        pk=object_pk,
    )

    cdr = get_object_or_404(obj.document_references, pk=casedocumentreference_pk)

    return view_application_file(
        user=request.user,
        application=application,
        related_file_model=File.objects,
        file_pk=cdr.document.pk,
        case_type=case_type,
    )
