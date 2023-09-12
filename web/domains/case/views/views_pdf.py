from typing import ClassVar

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.views.generic import View

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import view_application_file
from web.models import Country, File, Process
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest, DocumentTypes
from web.utils.pdf import PdfGenerator

from .mixins import ApplicationTaskMixin


class DocumentPreviewBase(ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View):
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
    permission_required = [Perms.sys.ilb_admin]

    document_types: ClassVar[list[DocumentTypes]]
    output_filename: ClassVar[str]

    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        self.set_application_and_task()

        document_type = self.kwargs["document_type"]

        if document_type not in self.document_types:
            raise ValueError(f"Unable to preview document_type: {document_type}")

        country_pk = self.kwargs.get("country_pk")

        pdf_gen = PdfGenerator(
            application=self.application,
            doc_pack=document_pack.pack_latest_get(self.application),
            doc_type=document_type,
            country=country_pk and Country.objects.get(pk=country_pk),
        )

        # TODO: Remove this when all the pdfs have been created
        # Useful when debugging pdf layout
        if "html" in self.request.GET:
            html = pdf_gen.get_document_html()
            return HttpResponse(html)

        return return_pdf(pdf_gen, self.output_filename)


class PreviewLicenceView(DocumentPreviewBase):
    document_types = [DocumentTypes.LICENCE_PREVIEW, DocumentTypes.LICENCE_PRE_SIGN]
    output_filename = "Licence-Preview.pdf"


class PreviewCoverLetterView(DocumentPreviewBase):
    document_types = [DocumentTypes.COVER_LETTER_PREVIEW, DocumentTypes.COVER_LETTER_PRE_SIGN]
    output_filename = "CoverLetter-Preview.pdf"


class PreviewCertificateView(DocumentPreviewBase):
    document_types = [DocumentTypes.CERTIFICATE_PREVIEW, DocumentTypes.CERTIFICATE_PRE_SIGN]
    output_filename = "Certificate-Preview.pdf"


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
    )
