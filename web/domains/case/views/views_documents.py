from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, FormView, View
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import DownloadDFLCaseDocumentsForm
from web.domains.case.services import document_pack
from web.domains.case.types import DocumentPack
from web.domains.case.utils import get_case_page_title
from web.flow.models import ProcessTypes
from web.mail.emails import send_constabulary_deactivated_firearms_email
from web.mail.url_helpers import get_constabulary_document_download_view_url
from web.models import (
    CaseDocumentReference,
    Constabulary,
    DFLApplication,
    ImportApplication,
    ImportApplicationDownloadLink,
    ImportApplicationLicence,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import create_presigned_url, get_file_from_s3
from web.utils.sentry import capture_exception


@method_decorator(ratelimit(key="ip", rate="10/m", method=UNSAFE, block=True), name="post")
@method_decorator(ratelimit(key="ip", rate="20/m", method="GET", block=True), name="get")
class DownloadDFLCaseDocumentsFormView(FormView):
    """View to see all documents relating to an import application.

    View does not require a logged-in user, it instead asks a user to enter information
    relating to the case.
    """

    # FormView config
    form_class = DownloadDFLCaseDocumentsForm
    template_name = "web/domains/case/download-case-documents.html"
    http_method_names = ["get", "post"]

    licence_date_format = "%d %b %Y"

    # We don't want to see the cookie banner / enable the JS
    extra_context = {"gtm_enabled": False}

    def get_initial(self) -> dict:
        """Load the form using query params from the request."""

        initial = super().get_initial()

        return initial | {
            "email": self.request.GET.get("email"),
            "constabulary": self.request.GET.get("constabulary"),
            "check_code": self.request.GET.get("check_code"),
        }

    def get_form_kwargs(self) -> dict[str, Any]:
        # Supply the code to the form.
        # Ensures we can only ever load a ImportApplicationDownloadLink record
        # associated with the code in the URL.
        return super().get_form_kwargs() | {
            "code": self.kwargs["code"],
        }

    def form_valid(self, form: DownloadDFLCaseDocumentsForm) -> HttpResponse:
        link: ImportApplicationDownloadLink = form.link  # type: ignore[assignment]

        # Load case documents here
        pack: ImportApplicationLicence = link.licence
        application = link.licence.import_application.get_specific_model()
        context = {
            "doc_pack": pack,
            "process": application,
            "application_type": ProcessTypes(application.process_type).label,
            "licence": {
                "case_reference": pack.case_reference,
                "variation_request": pack.case_reference.split("/")[3:],
                "issue_paper_licence_only": pack.issue_paper_licence_only,
                "licence_start_date": pack.licence_start_date.strftime(self.licence_date_format),
                "licence_end_date": pack.licence_end_date.strftime(self.licence_date_format),
                "case_completion_date": pack.case_completion_datetime.strftime(
                    self.licence_date_format
                ),
                "documents": [
                    {
                        "name": doc.get_document_type_display(),
                        "reference": doc.reference,
                        "url": create_presigned_url(doc.document.path, 60 * 5),
                    }
                    for doc in document_pack.doc_ref_documents_all(pack)
                ],
            },
        }

        # Reset the failure count
        link.failure_count = 0
        link.save()

        return self.render_to_response(self.get_context_data(form=form, **context))

    def form_invalid(self, form: DownloadDFLCaseDocumentsForm) -> HttpResponse:
        if form.link:
            link = form.link

            if link.failure_count < ImportApplicationDownloadLink.FAILURE_LIMIT:
                link.failure_count = F("failure_count") + 1
                link.save()
                # failure_count is updated when sql is executed, therefore refresh value from db
                link.refresh_from_db()

            if link.failure_count == ImportApplicationDownloadLink.FAILURE_LIMIT:
                link.expired = True
                link.save()

        return super().form_invalid(form)


@method_decorator(ratelimit(key="ip", rate="10/m", method=UNSAFE, block=True), name="post")
class RegenerateDFLCaseDocumentsDownloadLinkView(View):
    http_method_names = ["post"]

    def post(self, request: HttpResponse, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            link = ImportApplicationDownloadLink.objects.get(code=kwargs["code"])
            application: DFLApplication = link.licence.import_application.get_specific_model()

            # Expire the old one (if it wasn't already)
            link.expired = True
            link.save()

            # Resend the new one
            send_constabulary_deactivated_firearms_email(application)

        except ObjectDoesNotExist:
            pass

        except Exception:
            # This view should never fail.
            # We may be interested in errors other than ObjectDoesNotExist
            capture_exception()

        messages.info(request, "If the case exists a new email has been generated.")

        return redirect(
            reverse("case:download-dfl-case-documents", kwargs={"code": self.kwargs.get("code")})
        )


# Note: Not currently in use (replaced by DownloadDFLCaseDocumentsFormView)
class BaseConstabularyDocumentView(PermissionRequiredMixin, LoginRequiredMixin):
    permission_required = [Perms.page.view_documents_constabulary]

    def has_permission(self) -> bool:
        has_required_permissions = super().has_permission()
        if not has_required_permissions:
            return False

        constabularies: QuerySet[Constabulary] = get_objects_for_user(
            self.request.user,
            [Perms.obj.constabulary.verified_fa_authority_editor],
            Constabulary.objects.filter(is_active=True),
        )
        if constabularies:
            return self.is_application_linked_to_constabularies(constabularies)
        return False

    def is_application_linked_to_constabularies(
        self, constabularies: QuerySet[Constabulary]
    ) -> bool:
        application = self.get_object().get_specific_model()
        match application.process_type:
            case ProcessTypes.FA_DFL:
                return application.constabulary in constabularies
            case _:
                return False

    def get_document_pack(self, application: ImportApplication) -> DocumentPack:
        return document_pack.pack_issued_get_all(application).get(pk=self.kwargs["doc_pack_pk"])


# Note: Not currently in use (replaced by DownloadDFLCaseDocumentsFormView)
class ConstabularyDocumentView(BaseConstabularyDocumentView, DetailView):
    """View to view case documents relating to an application.

    Used by Constabulary Contact Users.
    """

    template_name = "web/domains/case/view-case-documents.html"
    model = ImportApplication
    pk_url_kwarg = "application_pk"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        application = self.object.get_specific_model()
        case_type = "import"
        context["page_title"] = get_case_page_title(case_type, application, "Issued Documents")
        context["process"] = application
        context["case_type"] = case_type
        context["org"] = application.importer
        return context | self.get_document_context_data(application)

    def get_document_context_data(self, application: ImportApplication) -> dict[str, Any]:
        at = application.application_type
        doc_pack = self.get_document_pack(application)
        licence_cdr = document_pack.doc_ref_licence_get(doc_pack)
        cover_letter_cdr = document_pack.doc_ref_cover_letter_get(doc_pack)

        return {
            "issue_date": doc_pack.case_completion_datetime,
            "is_import": True,
            "document_reference": application.reference,
            "type_label": at.get_type_display(),
            "licence_url": get_constabulary_document_download_view_url(
                application, doc_pack, licence_cdr
            ),
            "cover_letter_flag": True,
            "cover_letter_url": get_constabulary_document_download_view_url(
                application, doc_pack, cover_letter_cdr
            ),
        }


# Note: Not currently in use (replaced by DownloadDFLCaseDocumentsFormView)
class ConstabularyDocumentDownloadView(BaseConstabularyDocumentView, DetailView):
    model = ImportApplication
    pk_url_kwarg = "application_pk"

    def has_permission(self) -> bool:
        has_required_permissions = super().has_permission()
        if not has_required_permissions:
            return False
        application = self.get_object().get_specific_model()
        doc_pack = self.get_document_pack(application)
        if doc_pack and self.kwargs["cdr_pk"] in doc_pack.document_references.values_list(
            "pk", flat=True
        ):
            return True
        return False

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        cdr = CaseDocumentReference.objects.get(pk=kwargs["cdr_pk"])
        file_content = get_file_from_s3(cdr.document.path)
        response = HttpResponse(content=file_content, content_type=cdr.document.content_type)
        response["Content-Disposition"] = f'attachment; filename="{cdr.document.filename}"'
        return response
