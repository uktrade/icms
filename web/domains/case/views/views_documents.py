from typing import Any, ClassVar, TypeAlias

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, View
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit

from web.domains.case.forms import (
    DownloadCaseEmailDocumentsForm,
    DownloadDFLCaseDocumentsForm,
)
from web.domains.case.services import document_pack
from web.domains.case.types import ApplicationsWithCaseEmail, DownloadLink
from web.domains.case.utils import case_documents_metadata
from web.flow.models import ProcessTypes
from web.mail.constants import CaseEmailCodes
from web.mail.emails import (
    send_case_email,
    send_constabulary_deactivated_firearms_email,
)
from web.models import (
    CaseEmail,
    CaseEmailDownloadLink,
    ConstabularyLicenceDownloadLink,
    ExportApplication,
    ImportApplication,
    ImportApplicationLicence,
)
from web.utils import datetime_format
from web.utils.s3 import create_presigned_url
from web.utils.sentry import capture_exception

DownloadLinkForm: TypeAlias = DownloadCaseEmailDocumentsForm | DownloadDFLCaseDocumentsForm


@method_decorator(ratelimit(key="ip", rate="10/m", method="GET", block=True), name="get")
@method_decorator(ratelimit(key="ip", rate="20/m", method=UNSAFE, block=True), name="post")
class DownloadLinkFormViewBase(FormView):
    """Base class for views that allow users to download documents without logging in to ICMS.

    User are asked to enter information relating to the case before seeing the documents.
    """

    # FormView config
    http_method_names = ["get", "post"]

    # We don't want to see the cookie banner / enable the JS
    extra_context = {"gtm_enabled": False}

    def get_initial(self) -> dict:
        """Load the form using query params from the request."""

        initial = super().get_initial()

        return initial | {
            "email": self.request.GET.get("email"),
            "check_code": self.request.GET.get("check_code"),
        }

    def get_form_kwargs(self) -> dict[str, Any]:
        # Supply the code to the form.
        # Ensures we can only ever load a DownloadLink record
        # associated with the code in the URL.
        return super().get_form_kwargs() | {
            "code": self.kwargs["code"],
        }

    def form_valid(self, form: DownloadLinkForm) -> HttpResponse:
        link: DownloadLink = form.link  # type: ignore[assignment]

        # Reset the failure count
        link.failure_count = 0
        link.save()

        context = self.get_form_valid_context(form)
        return self.render_to_response(self.get_context_data(**context))

    def get_form_valid_context(self, form: DownloadLinkForm) -> dict[str, Any]:
        return {}

    def form_invalid(self, form: DownloadLinkForm) -> HttpResponse:
        if form.link:
            link = form.link

            if link.failure_count < link.FAILURE_LIMIT:
                link.failure_count = F("failure_count") + 1
                link.save()
                # failure_count is updated when sql is executed, therefore refresh value from db
                link.refresh_from_db()

            if link.failure_count == link.FAILURE_LIMIT:
                link.expired = True
                link.save()

        return super().form_invalid(form)


class DownloadCaseEmailDocumentsFormView(DownloadLinkFormViewBase):
    """View to see supporting documents relating to an application with case emails.

    The application types that support case emails with attachments are as follows:
        - DFLApplication
        - OpenIndividualLicenceApplication
        - SILApplication
        - NuclearMaterialApplication
        - SanctionsAndAdhocApplication
        - CertificateOfGoodManufacturingPracticeApplication

    View does not require a logged-in user, it instead asks a user to enter information
    relating to the case.
    """

    form_class = DownloadCaseEmailDocumentsForm
    template_name = "web/domains/case/download-case-email-documents.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context | {
            "regenerate_documents_link": reverse(
                "case:regenerate-case-email-documents-link", kwargs={"code": self.kwargs["code"]}
            )
        }

    def get_form_valid_context(self, form: DownloadCaseEmailDocumentsForm) -> dict[str, Any]:
        link: CaseEmailDownloadLink = form.link  # type: ignore[assignment]
        application = self.get_application(link.case_email)

        # Importer / Exporter details
        match application:
            case ExportApplication():
                context = {
                    "exporter": {
                        "name": application.exporter.name,
                        "office_address": application.exporter_office.address,
                        "office_postcode": application.exporter_office.postcode,
                    }
                }
            case ImportApplication():
                context = {
                    "importer": {
                        "name": application.importer.name,
                        "office_address": application.importer_office.address,
                        "office_postcode": application.importer_office.postcode,
                    }
                }
            case _:
                raise ValueError("Email attachments not supported for {case_email.template_code}.")

        is_firearms_application = application.process_type in [
            ProcessTypes.FA_OIL,
            ProcessTypes.FA_DFL,
            ProcessTypes.FA_SIL,
        ]

        return context | {
            "is_firearms_application": is_firearms_application,
            "file_metadata": case_documents_metadata(application),
            "documents": [
                {
                    "file": doc,
                    "url": create_presigned_url(doc.path),
                }
                for doc in link.case_email.attachments.all()
            ],
        }

    @staticmethod
    def get_application(case_email: CaseEmail) -> ApplicationsWithCaseEmail:
        match case_email.template_code:
            case CaseEmailCodes.BEIS_CASE_EMAIL:
                return ExportApplication.objects.get(case_emails=case_email).get_specific_model()
            case (
                CaseEmailCodes.CONSTABULARY_CASE_EMAIL
                | CaseEmailCodes.NMIL_CASE_EMAIL
                | CaseEmailCodes.SANCTIONS_CASE_EMAIL
            ):
                return ImportApplication.objects.get(case_emails=case_email).get_specific_model()
            case _:
                raise ValueError(f"Email attachments not supported for {case_email.template_code}.")


class DownloadDFLCaseDocumentsFormView(DownloadLinkFormViewBase):
    """View to see all documents relating to an import application.

    View does not require a logged-in user, it instead asks a user to enter information
    relating to the case.
    """

    # FormView config
    form_class = DownloadDFLCaseDocumentsForm
    template_name = "web/domains/case/download-case-documents.html"
    licence_date_format = "%d %b %Y"

    def get_initial(self) -> dict:
        """Load the form using query params from the request."""

        initial = super().get_initial()

        return initial | {
            "constabulary": self.request.GET.get("constabulary"),
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context | {
            "regenerate_documents_link": reverse(
                "case:regenerate-dfl-case-documents-link", kwargs={"code": self.kwargs["code"]}
            )
        }

    def get_form_valid_context(self, form: DownloadDFLCaseDocumentsForm) -> dict[str, Any]:
        link: ConstabularyLicenceDownloadLink = form.link  # type: ignore[assignment]
        pack: ImportApplicationLicence = link.licence
        application = link.licence.import_application.get_specific_model()

        return {
            "doc_pack": pack,
            "process": application,
            "application_type": ProcessTypes(application.process_type).label,
            "licence": {
                "case_reference": pack.case_reference,
                "variation_request": pack.case_reference.split("/")[3:],
                "issue_paper_licence_only": pack.issue_paper_licence_only,
                "licence_start_date": pack.licence_start_date.strftime(self.licence_date_format),
                "licence_end_date": pack.licence_end_date.strftime(self.licence_date_format),
                "case_completion_date": datetime_format(
                    pack.case_completion_datetime, self.licence_date_format
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


@method_decorator(ratelimit(key="ip", rate="10/m", method=UNSAFE, block=True), name="post")
class RegenerateDownloadLinkViewBase(View):
    http_method_names = ["post"]
    link_class: ClassVar[type[ConstabularyLicenceDownloadLink | CaseEmailDownloadLink]]
    download_url_name: ClassVar[str]

    def resend_email(self, link: DownloadLink) -> None:
        raise NotImplementedError("Method to resend email must be defined.")

    def post(self, request: HttpResponse, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            link = self.link_class.objects.get(code=kwargs["code"])

            # Expire the old one (if it wasn't already)
            link.expired = True
            link.save()

            self.resend_email(link)

        except ObjectDoesNotExist:
            pass

        except Exception:
            # This view should never fail.
            # We may be interested in errors other than ObjectDoesNotExist
            capture_exception()

        messages.info(request, "If the case exists a new email has been generated.")

        return redirect(reverse(self.download_url_name, kwargs={"code": self.kwargs.get("code")}))


class RegenerateDFLCaseDocumentsDownloadLinkView(RegenerateDownloadLinkViewBase):
    download_url_name = "case:download-dfl-case-documents"
    link_class = ConstabularyLicenceDownloadLink

    def resend_email(self, link: ConstabularyLicenceDownloadLink) -> None:
        application = link.licence.import_application.get_specific_model()
        send_constabulary_deactivated_firearms_email(application)


class RegenerateCaseEmailDocumentsDownloadLinkView(RegenerateDownloadLinkViewBase):
    download_url_name = "case:download-case-email-documents"
    link_class = CaseEmailDownloadLink

    def resend_email(self, link: CaseEmailDownloadLink) -> None:
        send_case_email(link.case_email, self.request.user)
