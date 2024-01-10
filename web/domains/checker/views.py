from django.http import HttpResponse
from django.shortcuts import render

from web.flow.models import ProcessTypes
from web.models import (
    CaseDocumentReference,
    ExportApplication,
    ExportApplicationCertificate,
)
from web.sites import require_exporter
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import create_presigned_url

from .forms import CertificateCheckForm


def _get_export_application_goods(app: ExportApplication) -> str:
    match app.process_type:
        case ProcessTypes.GMP:
            return "N/A"
        case ProcessTypes.CFS:
            cfs = app.certificateoffreesaleapplication
            product_names = cfs.schedules.values_list("products__product_name", flat=True)
            return ", ".join(goods for goods in product_names)
        case ProcessTypes.COM:
            return app.certificateofmanufactureapplication.product_name
        case _:
            raise ValueError(f"{app.process_type} not an ExportApplication process type.")


@require_exporter(check_permission=False)
def check_certificate(
    request: AuthenticatedHttpRequest,
) -> HttpResponse:
    context = {
        "page_title": "Certificate Checker",
        "document": None,
    }

    if request.method == "POST":
        form = CertificateCheckForm(request.POST)

        if form.is_valid():
            check = form.clean()
            reference = check["certificate_reference"]
            code = check["certificate_code"]

            try:
                document = CaseDocumentReference.objects.get(reference=reference, check_code=code)
                context["document"] = document
                context["country"] = document.reference_data.country.name

                cert = ExportApplicationCertificate.objects.get(document_references=document)
                app = cert.export_application
                context["exporter"] = app.exporter.name

                context["issue_date"] = cert.case_completion_datetime.strftime("%d %B %Y")
                context["goods"] = _get_export_application_goods(app)

                url = create_presigned_url(document.document.path)
                context["download_url"] = url

                validity = "Revoked" if cert.status == cert.Status.REVOKED else "Valid"
                context["is_valid"] = validity

                context["success_message"] = f"Certificate {reference} is valid."

            except CaseDocumentReference.DoesNotExist:
                context["warning_message"] = (
                    f"Certificate {reference} could not be found with the given code {code}. "
                    f"Please ensure the reference and code is entered correctly and try again."
                )
        else:
            context["warning_message"] = "You must enter a certificate reference and code."
    else:
        form_data = {
            "certificate_reference": request.GET.get("CERTIFICATE_REFERENCE"),
            "certificate_code": request.GET.get("CERTIFICATE_CODE"),
        }
        form = CertificateCheckForm(form_data)

    context["form"] = form

    return render(request, "web/domains/checker/certificate-checker.html", context)
