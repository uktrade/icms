from collections.abc import Iterator
from typing import Any, Optional, TypeAlias

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from web.domains.case.services import document_pack, reference
from web.flow.models import ProcessTypes
from web.mail.emails import send_application_update_response_email
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    DFLApplication,
    ExportApplication,
    ImportApplication,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    Task,
    UpdateRequest,
    User,
)
from web.permissions import AppChecker
from web.types import AuthenticatedHttpRequest
from web.utils import datetime_format
from web.utils.s3 import get_file_from_s3

from .types import (
    ApplicationsWithCaseEmail,
    CaseDocumentsMetadata,
    ImpOrExp,
    ImpOrExpOrAccess,
)


def end_process_task(task: Task, user: Optional["User"] = None) -> None:
    """End the supplied task.

    :param task: Task instance
    :param user: User who ended the task
    """

    task.is_active = False
    task.finished = timezone.now()

    if user:
        task.owner = user

    task.save()


def view_application_file(
    user: User, application: ImpOrExp, related_file_model: Any, file_pk: int
) -> HttpResponse:
    checker = AppChecker(user, application)

    if not checker.can_view():
        raise PermissionDenied

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


def get_case_page_title(case_type: str, application: ImpOrExpOrAccess, page: str) -> str:
    if case_type in ("import", "export"):
        return f"{ProcessTypes(application.process_type).label} - {page}"
    elif case_type == "access":
        return f"Access Request - {page}"
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def get_application_form(
    application: ImpOrExp,
    request: AuthenticatedHttpRequest,
    edit_form: type[forms.ModelForm],
    submit_form: type[forms.ModelForm],
) -> forms.ModelForm:
    """Create a form instance - Used in all edit application views."""

    if request.method == "POST":
        form = edit_form(data=request.POST, instance=application)
    else:
        initial = {} if application.contact else {"contact": request.user}
        form_kwargs = {"instance": application, "initial": initial}

        # query param to fully validate the form.
        if "validate" in request.GET:
            form_kwargs["data"] = model_to_dict(application)
            form = submit_form(**form_kwargs)
        else:
            form = edit_form(**form_kwargs)

    return form


def submit_application(app: ImpOrExp, request: AuthenticatedHttpRequest, task: Task) -> None:
    """Helper function to submit all types of application."""

    if not app.reference:
        app.reference = reference.get_application_case_reference(
            request.icms.lock_manager, application=app
        )

    if app.case_owner:
        # Only change to processing if it's not a variation request
        if app.status != app.Statuses.VARIATION_REQUESTED:
            app.status = app.Statuses.PROCESSING
    else:
        app.status = app.Statuses.SUBMITTED

    current_date_time = timezone.now()
    if not app.submit_datetime:
        app.submit_datetime = current_date_time
    app.last_submit_datetime = current_date_time
    app.submitted_by = request.user
    app.update_order_datetime()
    app.save()

    # Mark an open update request as responded.
    active_update_request = app.update_requests.filter(
        status=UpdateRequest.Status.UPDATE_IN_PROGRESS, is_active=True
    ).first()

    if active_update_request:
        # Mark update request as responded
        active_update_request.status = UpdateRequest.Status.RESPONDED
        active_update_request.save()

        # Notify caseworker / ILB
        send_application_update_response_email(app)

    task.is_active = False
    task.finished = timezone.now()
    task.save()

    # Only create a PROCESS Task if one doesn't exist.
    # One will already exist if the applicant is submitting an application after an
    # update request from ILB.
    Task.objects.get_or_create(
        process=app, task_type=Task.TaskType.PROCESS, is_active=True, defaults={"previous": task}
    )


def redirect_after_submit(app: ImpOrExp, request: AuthenticatedHttpRequest) -> HttpResponse:
    """Called after submitting an application"""

    msg = (
        "Your application has been submitted."
        f" The reference number assigned to this case is {app.get_reference()}."
    )
    messages.success(request, msg)

    return redirect(reverse("workbasket"))


def application_history(app_reference: str, is_import: bool = True) -> None:
    """Debug method to print the history of the application.

    >>> import os; import importlib as im; from web.domains.case import utils
    >>> os.system("clear"); im.reload(utils); utils.application_history("IMA/2024/00001")
    """

    if is_import:
        app = ImportApplication.objects.get(reference__startswith=app_reference)
    else:
        app = ExportApplication.objects.get(reference__startswith=app_reference)

    app = app.get_specific_model()

    print("*-" * 40)
    print(f"Current status: {app.get_status_display()}")

    all_tasks = app.tasks.all().order_by("created")
    active = all_tasks.filter(is_active=True)

    print("\nActive Tasks in order:")
    for t in active:
        _print_task(t)

    print("\nAll tasks in order:")
    for t in all_tasks:
        _print_task(t)

    print("*-" * 40)
    print("Document Packs:")
    for p in document_pack._get_qm(app).order_by("created_at"):
        print(f"\t- {p}")
        for df in p.document_references.all():
            print(f"\t\t- {df}")


def _print_task(t: Task) -> None:
    task_type = t.get_task_type_display()
    created = datetime_format(t.created, "%Y/%m/%d %H:%M:%S")
    finished = datetime_format(t.finished, "%Y-%m-%d %H:%M:%S") if t.finished else ""

    print(f"\tTask: {task_type}, created={created}, finished={finished}")


def case_documents_metadata(application: ApplicationsWithCaseEmail) -> CaseDocumentsMetadata:
    """Return metadata for all the documents linked to a case.

    Useful when only the File.pk is known (as they are in CaseEmail.attachments)
    This should always include all file, not just active ones, in case we are looking at old cases.
    """

    match application:
        case SILApplication():
            file_metadata = get_fa_sil_file_data(application)

        case OpenIndividualLicenceApplication():
            file_metadata = get_fa_oil_file_data(application)

        case DFLApplication():
            file_metadata = get_fa_dfl_file_data(application)

        case SanctionsAndAdhocApplication():
            file_metadata = get_sanctions_file_data(application)

        case CertificateOfFreeSaleApplication():
            # CFS uses case emails however it has no linked files.
            return {}

        case CertificateOfGoodManufacturingPracticeApplication():
            file_metadata = get_gmp_file_data(application)

        case _:
            raise ValueError(
                f"Application {application.application_type.get_type_display()} not supported."
            )

    return {pk: metadata for pk, metadata in file_metadata}


FileMetadata: TypeAlias = Iterator[tuple[int, dict[str, str]]]


def get_fa_sil_file_data(app: SILApplication) -> FileMetadata:
    #
    # Section 5 authority documents
    #
    for cert in app.verified_section5.all():
        for f in cert.files.all():
            yield (
                f.pk,
                {
                    "title": "Verified Section 5 Authority",
                    "reference": cert.reference,
                    "certificate_type": "Section 5 Authority",
                    "issuing_constabulary": "",
                    "url": reverse(
                        "importer-section5-view-document",
                        kwargs={"section5_pk": cert.pk, "document_pk": f.pk},
                    ),
                },
            )

    for f in app.user_section5.all():
        yield (
            f.pk,
            {
                "title": "User Uploaded Section 5 Authority",
                "reference": "",
                "certificate_type": "Section 5 Authority",
                "issuing_constabulary": "",
                "url": reverse(
                    "import:fa-sil:view-section5-document",
                    kwargs={"application_pk": app.pk, "section5_pk": f.pk},
                ),
            },
        )

    #
    # Verified authority documents
    #
    for cert in app.verified_certificates.all():
        for f in cert.files.all():
            yield (
                f.pk,
                {
                    "title": "Verified Firearms Authority",
                    "reference": cert.reference,
                    "certificate_type": cert.get_certificate_type_display(),
                    "issuing_constabulary": cert.issuing_constabulary.name,
                    "url": reverse(
                        "importer-firearms-view-document",
                        kwargs={"firearms_pk": cert.pk, "document_pk": f.pk},
                    ),
                },
            )

    for f in app.user_imported_certificates.all():
        yield (
            f.pk,
            {
                "title": "User Uploaded Verified Firearms Authority",
                "reference": f.reference,
                "certificate_type": f.get_certificate_type_display(),
                "issuing_constabulary": f.constabulary.name,
                "url": reverse(
                    "import:fa:view-certificate-document",
                    kwargs={"application_pk": app.pk, "certificate_pk": f.pk},
                ),
            },
        )


def get_fa_oil_file_data(app: OpenIndividualLicenceApplication) -> FileMetadata:
    #
    # Verified authority documents
    #
    for cert in app.verified_certificates.all():
        for f in cert.files.all():
            yield (
                f.pk,
                {
                    "title": "Verified Firearms Authority",
                    "reference": cert.reference,
                    "certificate_type": cert.get_certificate_type_display(),
                    "issuing_constabulary": cert.issuing_constabulary.name,
                    "url": reverse(
                        "importer-firearms-view-document",
                        kwargs={"firearms_pk": cert.pk, "document_pk": f.pk},
                    ),
                },
            )

    for f in app.user_imported_certificates.all():
        yield (
            f.pk,
            {
                "title": "User Uploaded Verified Firearms Authority",
                "reference": f.reference,
                "certificate_type": f.get_certificate_type_display(),
                "issuing_constabulary": f.constabulary.name,
                "url": reverse(
                    "import:fa:view-certificate-document",
                    kwargs={"application_pk": app.pk, "certificate_pk": f.pk},
                ),
            },
        )


def get_fa_dfl_file_data(app: DFLApplication) -> FileMetadata:
    for f in app.goods_certificates.all():
        yield (
            f.pk,
            {
                "title": "Firearms Certificate",
                "reference": f.deactivated_certificate_reference,
                "certificate_type": "Deactivation Certificate",
                "issuing_constabulary": app.constabulary.name,
                "url": reverse(
                    "import:fa-dfl:view-goods",
                    kwargs={"application_pk": app.pk, "document_pk": f.pk},
                ),
            },
        )


def get_sanctions_file_data(app: SanctionsAndAdhocApplication) -> FileMetadata:
    for f in app.supporting_documents.all():
        yield (
            f.pk,
            {
                "file_type": "Supporting Documents",
                "url": reverse(
                    "import:sanctions:view-supporting-document",
                    kwargs={"application_pk": app.pk, "document_pk": f.pk},
                ),
            },
        )


def get_gmp_file_data(app: CertificateOfGoodManufacturingPracticeApplication) -> FileMetadata:
    for f in app.supporting_documents.all():
        yield (
            f.pk,
            {
                "file_type": f.get_file_type_display(),
                "url": reverse(
                    "export:gmp-view-document",
                    kwargs={"application_pk": app.pk, "document_pk": f.pk},
                ),
            },
        )
