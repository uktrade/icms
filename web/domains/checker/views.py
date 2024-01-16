from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from web.flow.models import ProcessTypes
from web.models import (
    CaseDocumentReference,
    ExportApplication,
    ExportApplicationCertificate,
)
from web.sites import require_exporter
from web.utils.s3 import create_presigned_url

from .forms import CertificateCheckForm


def _get_export_application_goods(app: ExportApplication) -> str:
    match app.process_type:
        case ProcessTypes.GMP:
            return "N/A"
        case ProcessTypes.CFS:
            cfs = app.get_specific_model()
            product_names = cfs.schedules.values_list("products__product_name", flat=True)
            return ", ".join(goods for goods in product_names)
        case ProcessTypes.COM:
            return app.get_specific_model().product_name
        case _:
            raise ValueError(f"{app.process_type} not an ExportApplication process type.")


class CheckCertificateView(FormView):
    form_class = CertificateCheckForm
    template_name = "web/domains/checker/certificate-checker.html"

    @method_decorator(require_exporter(check_permission=False))
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["document"] = context.get("document")
        context["page_title"] = "Certificate Checker"

        return context

    def get_initial(self) -> dict[str, Any]:
        return {
            "certificate_reference": self.request.GET.get("CERTIFICATE_REFERENCE"),
            "certificate_code": self.request.GET.get("CERTIFICATE_CODE"),
            "country": self.request.GET.get("COUNTRY"),
            "organisation_name": self.request.GET.get("ORGANISATION"),
        }

    def form_valid(self, form: CertificateCheckForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        check = form.clean()
        reference = check["certificate_reference"]
        code = check["certificate_code"]
        country = check["country"]
        org_name = check["organisation_name"]

        try:
            document = CaseDocumentReference.objects.get(
                reference=reference,
                check_code=code,
                reference_data__country=country,
            )

            # GMP Certificates have the manufacturer name on the certificate rather than the exporter
            if reference.startswith("GMP"):
                cert = ExportApplicationCertificate.objects.get(
                    document_references=document,
                    export_application__certificateofgoodmanufacturingpracticeapplication__manufacturer_name__iexact=org_name,
                )
            else:
                cert = ExportApplicationCertificate.objects.get(
                    document_references=document,
                    export_application__exporter__name__iexact=org_name,
                )

            context["document"] = document
            context["country"] = country.name

            app = cert.export_application
            context["exporter"] = app.exporter.name

            context["issue_date"] = cert.case_completion_datetime.strftime("%d %B %Y")
            context["goods"] = _get_export_application_goods(app)

            validity = "Revoked" if cert.status == cert.Status.REVOKED else "Valid"
            context["is_valid"] = validity

            if cert.status == cert.Status.REVOKED:
                context["error_message"] = f"Certificate {reference} has been revoked."
            else:
                url = create_presigned_url(document.document.path)
                context["download_url"] = url or "Error"

                if not url:
                    warning = "A download link failed to generate. Please resubmit the form."
                    context["warning_message"] = warning
                else:
                    context["success_message"] = f"Certificate {reference} is valid."

        except (CaseDocumentReference.DoesNotExist, ExportApplicationCertificate.DoesNotExist):
            context["warning_message"] = (
                f"Certificate {reference} could not be found with the given code {code}. "
                f"Please ensure all details are entered correctly and try again."
            )

        # Renders page with extra context when form submission valid
        return self.render_to_response(context)

    def form_invalid(self, form: CertificateCheckForm) -> HttpResponse:
        return self.render_to_response(
            self.get_context_data(form=form, warning_message="You must enter all details.")
        )
