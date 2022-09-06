from itertools import product
from typing import TYPE_CHECKING, Any, Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View
from guardian.shortcuts import get_users_with_perms

from web.domains.case import forms
from web.domains.case.app_checks import get_app_errors
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportCertificateCaseDocumentReferenceData,
)
from web.domains.case.models import (
    CaseDocumentReference,
    CaseLicenceCertificateBase,
    VariationRequest,
)
from web.domains.case.services import reference
from web.domains.case.shared import ImpExpStatus
from web.domains.case.tasks import create_case_document_pack
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import (
    archive_application_licence_or_certificate,
    check_application_permission,
    end_process_task,
    get_application_current_task,
    get_case_page_title,
)
from web.domains.template.models import Template
from web.domains.user.models import User
from web.flow.models import ProcessTypes, Task
from web.models import WithdrawApplication
from web.notify.email import send_email
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import delete_file_from_s3, get_s3_client
from web.utils.validation import ApplicationErrors

from .mixins import ApplicationTaskMixin
from .utils import get_class_imp_or_exp, get_current_task_and_readonly_status

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.case._import.models import ImportApplicationLicence
    from web.domains.case.export.models import ExportApplicationCertificate
    from web.utils.lock_manager import LockManager


# "Applicant Case Management" Views
@login_required
@require_POST
def cancel_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)
        get_application_current_task(application, case_type, Task.TaskType.PREPARE)

        # the above accepts PROCESSING, we don't
        if application.status != model_class.Statuses.IN_PROGRESS:
            raise PermissionDenied

        application.delete()

        messages.success(request, "Application has been cancelled.")

        return redirect(reverse("workbasket"))


@login_required
def withdraw_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)
        application.check_expected_status(
            [ImpExpStatus.SUBMITTED, ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        )

        if request.method == "POST":
            form = forms.WithdrawForm(request.POST)

            if form.is_valid():
                withdrawal = form.save(commit=False)

                if case_type == "import":
                    withdrawal.import_application = application
                elif case_type == "export":
                    withdrawal.export_application = application

                withdrawal.status = WithdrawApplication.STATUS_OPEN
                withdrawal.request_by = request.user
                withdrawal.save()

                application.update_order_datetime()
                application.save()

                messages.success(
                    request,
                    "You have requested that this application be withdrawn. Your request has been sent to ILB.",
                )

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "process": application,
            "page_title": get_case_page_title(case_type, application, "Withdrawals"),
            "form": form,
            "withdrawals": application.withdrawals.filter(is_active=True),
            "case_type": case_type,
        }
        return render(request, "web/domains/case/withdraw.html", context)


@login_required
@require_POST
def archive_withdrawal(
    request: AuthenticatedHttpRequest, *, application_pk: int, withdrawal_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)
        application.check_expected_status(
            [ImpExpStatus.SUBMITTED, ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        )

        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)
        withdrawal.is_active = False
        withdrawal.save()

        messages.success(
            request, "You have retracted your request for this application to be withdrawn."
        )

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_withdrawals(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task, readonly_view = get_current_task_and_readonly_status(
            application, case_type, request.user, Task.TaskType.PROCESS
        )

        withdrawals = application.withdrawals.filter(is_active=True).order_by("-created_datetime")
        current_withdrawal = withdrawals.filter(status=WithdrawApplication.STATUS_OPEN).first()

        if request.method == "POST" and not readonly_view:
            form = forms.WithdrawResponseForm(request.POST, instance=current_withdrawal)

            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.response_by = request.user
                withdrawal.save()

                # withdrawal accepted - case is closed, else case still open
                if withdrawal.status == WithdrawApplication.STATUS_ACCEPTED:
                    if application.status == ImpExpStatus.VARIATION_REQUESTED:
                        application.status = ImpExpStatus.COMPLETED
                        # Close the open variation request if we are withdrawing the application / variation
                        vr = application.variation_requests.get(status=VariationRequest.OPEN)
                        vr.status = VariationRequest.WITHDRAWN
                        vr.reject_cancellation_reason = application.variation_refuse_reason
                        vr.closed_datetime = timezone.now()
                        vr.save()
                    else:
                        application.status = model_class.Statuses.WITHDRAWN
                        application.is_active = False

                    application.update_order_datetime()
                    application.save()

                    end_process_task(task, request.user)

                    return redirect(reverse("workbasket"))
                else:
                    end_process_task(task)

                    Task.objects.create(
                        process=application, task_type=Task.TaskType.PROCESS, previous=task
                    )

                    return redirect(
                        reverse(
                            "case:manage-withdrawals",
                            kwargs={"application_pk": application_pk, "case_type": case_type},
                        )
                    )
        else:
            form = forms.WithdrawResponseForm(instance=current_withdrawal)

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "process": application,
            "task": task,
            "page_title": get_case_page_title(case_type, application, "Withdrawals"),
            "form": form,
            "withdrawals": withdrawals,
            "current_withdrawal": current_withdrawal,
            "case_type": case_type,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/withdrawals.html",
            context=context,
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def take_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        application.get_task(
            expected_state=[
                model_class.Statuses.SUBMITTED,
                model_class.Statuses.VARIATION_REQUESTED,
            ],
            task_type=Task.TaskType.PROCESS,
        )

        if application.status == model_class.Statuses.SUBMITTED:
            application.status = model_class.Statuses.PROCESSING

            if case_type == "import":
                # Licence start date is set when ILB Admin takes the case
                licence = application.get_most_recent_licence()
                if not licence.licence_start_date:
                    licence.licence_start_date = timezone.now().date()
                    licence.save()

            # TODO: Revisit when implementing ICMSLST-1169
            # We may need to create some more datetime fields

        application.case_owner = request.user
        application.update_order_datetime()
        application.save()

        return redirect(
            reverse(
                "case:manage", kwargs={"application_pk": application.pk, "case_type": case_type}
            )
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def release_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if application.status != model_class.Statuses.VARIATION_REQUESTED:
            application.status = model_class.Statuses.SUBMITTED

        application.case_owner = None
        application.update_order_datetime()
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task, readonly_view = get_current_task_and_readonly_status(
            application, case_type, request.user, Task.TaskType.PROCESS
        )

        if request.method == "POST" and not readonly_view:
            form = forms.CloseCaseForm(request.POST)

            if form.is_valid():
                application.status = model_class.Statuses.STOPPED
                application.save()

                end_process_task(task)

                if form.cleaned_data.get("send_email"):
                    template = Template.objects.get(template_code="STOP_CASE")

                    subject = template.get_title({"CASE_REFERENCE": application.pk})
                    body = template.get_content({"CASE_REFERENCE": application.pk})

                    if case_type == "import":
                        users = get_users_with_perms(
                            application.importer, only_with_perms_in=["is_contact_of_importer"]
                        ).filter(user_permissions__codename="importer_access")
                    else:
                        users = get_users_with_perms(
                            application.exporter, only_with_perms_in=["is_contact_of_exporter"]
                        ).filter(user_permissions__codename="exporter_access")

                    recipients = set(users.values_list("email", flat=True))

                    send_email(subject, body, recipients)

                messages.success(
                    request,
                    "This case has been stopped and removed from your workbasket."
                    " It will still be available from the search screen.",
                )

                return redirect(reverse("workbasket"))
        else:
            form = forms.CloseCaseForm()

        context = {
            "case_type": case_type,
            "process": application,
            "task": task,
            "page_title": get_case_page_title(case_type, application, "Manage"),
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request, template_name="web/domains/case/manage/manage.html", context=context
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def start_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """Authorise the application, in legacy this is called "Close Case Processing".

    `application.decision` is used to determine the next steps.
    """

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application_errors: ApplicationErrors = get_app_errors(application, case_type)

        if request.method == "POST" and not application_errors.has_errors():
            create_references = True

            if application.status == application.Statuses.VARIATION_REQUESTED:
                if (
                    application.is_import_application()
                    and application.variation_decision == application.REFUSE
                ):
                    vr = application.variation_requests.get(status=VariationRequest.OPEN)
                    next_task = None
                    application.status = model_class.Statuses.COMPLETED
                    vr.status = VariationRequest.REJECTED
                    vr.reject_cancellation_reason = application.variation_refuse_reason
                    vr.closed_datetime = timezone.now()

                    vr.save()

                    create_references = False
                else:
                    next_task = Task.TaskType.AUTHORISE

            else:
                if application.decision == application.REFUSE:
                    next_task = Task.TaskType.REJECTED
                    application.status = model_class.Statuses.COMPLETED
                    create_references = False

                else:
                    next_task = Task.TaskType.AUTHORISE
                    application.status = model_class.Statuses.PROCESSING

            application.update_order_datetime()
            application.save()

            end_process_task(task)

            if next_task:
                Task.objects.create(process=application, task_type=next_task, previous=task)

            if create_references:
                create_application_document_references(request.icms.lock_manager, application)
            else:
                archive_application_licence_or_certificate(application)

            return redirect(reverse("workbasket"))

        else:
            context = {
                "case_type": case_type,
                "process": application,
                "task": task,
                "page_title": get_case_page_title(case_type, application, "Authorisation"),
                "errors": application_errors if application_errors.has_errors() else None,
            }

            return render(
                request=request,
                template_name="web/domains/case/authorisation.html",
                context=context,
            )


def create_application_document_references(
    lock_manager: "LockManager", application: ImpOrExp
) -> None:
    """Create the document references for the draft licence."""

    if application.is_import_application():
        licence = application.get_most_recent_licence()

        if licence.status != CaseLicenceCertificateBase.Status.DRAFT:
            raise ValueError("Can only create references for a draft application")

        licence.document_references.get_or_create(
            document_type=CaseDocumentReference.Type.COVER_LETTER
        )

        if not licence.document_references.filter(
            document_type=CaseDocumentReference.Type.LICENCE
        ).exists():
            # Only call `get_import_licence_reference` if needed as it creates a record in CaseReference
            licence.document_references.create(
                document_type=CaseDocumentReference.Type.LICENCE,
                reference=reference.get_import_licence_reference(lock_manager, application),
            )
    else:
        _create_export_application_document_references(lock_manager, application)


def _create_export_application_document_references(
    lock_manager: "LockManager", application: ExportApplication
):
    """Creates document reference records for Export applications."""

    certificate = application.get_most_recent_certificate()

    if certificate.status != CaseLicenceCertificateBase.Status.DRAFT:
        raise ValueError("Can only create references for a draft application")

    # Clear all document references as they may have changed
    certificate.document_references.all().delete()

    if application.process_type in [ProcessTypes.COM, ProcessTypes.CFS]:
        app: Union[
            CertificateOfManufactureApplication, CertificateOfFreeSaleApplication
        ] = application.get_specific_model()

        for country in app.countries.all().order_by("name"):
            cdr: "CaseDocumentReference" = certificate.document_references.create(
                document_type=CaseDocumentReference.Type.CERTIFICATE,
                reference=reference.get_export_certificate_reference(lock_manager, app),
            )
            ExportCertificateCaseDocumentReferenceData.objects.create(
                case_document_reference=cdr, country=country
            )

    elif application.process_type == ProcessTypes.GMP:
        gmp_app: CertificateOfGoodManufacturingPracticeApplication = (
            application.get_specific_model()
        )
        countries = gmp_app.countries.all().order_by("name")
        brands = gmp_app.brands.all().order_by("brand_name")

        for country, brand in product(countries, brands):
            cdr = certificate.document_references.create(
                document_type=CaseDocumentReference.Type.CERTIFICATE,
                reference=reference.get_export_certificate_reference(lock_manager, gmp_app),
            )

            ExportCertificateCaseDocumentReferenceData.objects.create(
                case_document_reference=cdr, country=country, gmp_brand=brand
            )

    else:
        raise NotImplementedError(f"Unknown process_type: {application.process_type}")


@login_required
@sensitive_post_parameters("password")
@permission_required("web.ilb_admin", raise_exception=True)
def authorise_documents(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.AUTHORISE)

        if request.method == "POST":
            form = forms.AuthoriseForm(data=request.POST, request=request)

            if form.is_valid():
                end_process_task(task, request.user)
                Task.objects.create(
                    process=application, task_type=Task.TaskType.DOCUMENT_SIGNING, previous=task
                )

                application.update_order_datetime()
                application.save()

                # Queues all documents to be created
                create_case_document_pack(application, request.user)

                messages.success(
                    request,
                    f"Authorise Success: Application {application.reference} has been queued for document signing",
                )

                return redirect(reverse("workbasket"))

        else:
            form = forms.AuthoriseForm(request=request)

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "process": application,
            "task": task,
            "page_title": get_case_page_title(case_type, application, "Authorisation"),
            "form": form,
            "primary_recipients": _get_primary_recipients(application),
            "copy_recipients": _get_copy_recipients(application),
        }

        return render(
            request=request,
            template_name="web/domains/case/authorise-documents.html",
            context=context,
        )


class CheckCaseDocumentGenerationView(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View
):
    # View Config
    http_method_names = ["get"]

    # ApplicationTaskMixin Config
    current_status = [
        ImpExpStatus.PROCESSING,
        ImpExpStatus.VARIATION_REQUESTED,
        ImpExpStatus.COMPLETED,
    ]

    # PermissionRequiredMixin Config
    permission_required = ["web.ilb_admin"]

    def get(self, request: HttpRequest, *args, **kwargs) -> Any:
        self.set_application_and_task()

        active_tasks = self.application.get_active_task_list()

        reload_workbasket = False

        if (
            self.application.status == ImpExpStatus.COMPLETED
            or Task.TaskType.CHIEF_WAIT in active_tasks
        ):
            msg = "Documents generated successfully"
            reload_workbasket = True

        elif Task.TaskType.DOCUMENT_ERROR in active_tasks:
            msg = "Failed to generate documents"
            reload_workbasket = True

        elif Task.TaskType.DOCUMENT_SIGNING in active_tasks:
            msg = "Documents are still being generated"

        elif Task.TaskType.CHIEF_ERROR in active_tasks:
            msg = "Unable to send licence details to HMRC"
            reload_workbasket = True

        else:
            # TODO: Sent a sentry message instead to handle the error gracefully
            raise Exception("Unknown state for application")

        return JsonResponse(data={"msg": msg, "reload_workbasket": reload_workbasket})


@method_decorator(transaction.atomic, name="post")
class RecreateCaseDocumentsView(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View
):
    # View Config
    http_method_names = ["post"]

    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
    current_task_type = Task.TaskType.DOCUMENT_ERROR
    next_task_type = Task.TaskType.DOCUMENT_SIGNING

    # PermissionRequiredMixin Config
    permission_required = ["web.ilb_admin"]

    def post(self, request: HttpRequest, *args, **kwargs) -> Any:
        """Deletes existing draft PDFs and regenerates case document pack"""
        self.set_application_and_task()

        if self.application.is_import_application():
            l_or_c = self.application.get_most_recent_licence()
        else:
            l_or_c = self.application.get_most_recent_certificate()

        s3_client = get_s3_client()
        for cdr in l_or_c.document_references.all():
            if cdr.document and cdr.document.path:
                delete_file_from_s3(cdr.document.path, s3_client)

        self.update_application_tasks()
        create_case_document_pack(self.application, self.request.user)

        self.application.update_order_datetime()
        self.application.save()

        messages.success(
            request,
            f"Recreate Case Documents Success:"
            f" Application {self.application.reference} has been queued for document signing",
        )

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_document_packs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """ILB Admin view to view the application documents before authorising."""

    with transaction.atomic():
        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, "authorise")

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "process": application,
            "task": task,
            "page_title": get_case_page_title(case_type, application, "Authorisation"),
            "primary_recipients": _get_primary_recipients(application),
            "copy_recipients": _get_copy_recipients(application),
            **get_document_context(application),
        }

        return render(
            request=request,
            template_name="web/domains/case/document-packs.html",
            context=context,
        )


def get_document_context(
    application: ImpOrExp,
    issued_document: Union["ImportApplicationLicence", "ExportApplicationCertificate"] = None,
) -> dict[str, str]:
    at = application.application_type

    if application.is_import_application():
        licence = issued_document or application.get_most_recent_licence()
        licence_doc = licence.document_references.get(
            document_type=CaseDocumentReference.Type.LICENCE
        )
        cover_letter = licence.document_references.get(
            document_type=CaseDocumentReference.Type.COVER_LETTER
        )

        # If issued_document is not None then we are viewing completed documents
        if application.status == ImpExpStatus.COMPLETED or issued_document:
            licence_url = reverse(
                "case:view-case-document",
                kwargs={
                    "application_pk": application.id,
                    "case_type": "import",
                    "object_pk": licence.pk,
                    "casedocumentreference_pk": licence_doc.pk,
                },
            )
            cover_letter_url = reverse(
                "case:view-case-document",
                kwargs={
                    "application_pk": application.id,
                    "case_type": "import",
                    "object_pk": licence.pk,
                    "casedocumentreference_pk": cover_letter.pk,
                },
            )
        else:
            licence_url = reverse(
                "case:licence-pre-sign",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
            cover_letter_url = reverse(
                "case:preview-cover-letter",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )

        context = {
            "cover_letter_flag": at.cover_letter_flag,
            "type_label": at.Types(at.type).label,
            "customs_copy": at.type == at.Types.OPT,
            "is_cfs": False,
            "document_reference": licence_doc.reference,
            "licence_url": licence_url,
            "cover_letter_url": cover_letter_url,
        }
    else:
        certificate = issued_document or application.get_most_recent_certificate()
        certificate_docs = certificate.document_references.filter(
            document_type=CaseDocumentReference.Type.CERTIFICATE
        )
        document_reference = ", ".join(c.reference for c in certificate_docs)

        context = {
            "cover_letter_flag": False,
            "type_label": at.type,
            "customs_copy": False,
            "is_cfs": at.type_code == at.Types.FREE_SALE,
            "document_reference": document_reference,
            # TODO: Revisit when we can generate an export certificate
            # https://uktrade.atlassian.net/browse/ICMSLST-1406
            # https://uktrade.atlassian.net/browse/ICMSLST-1407
            # https://uktrade.atlassian.net/browse/ICMSLST-1408
            "certificate_links": [],
        }

    return context


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def cancel_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.AUTHORISE)

        if application.status != model_class.Statuses.VARIATION_REQUESTED:
            application.status = model_class.Statuses.PROCESSING

        application.update_order_datetime()
        application.save()

        end_process_task(task, request.user)

        Task.objects.create(process=application, task_type=Task.TaskType.PROCESS, previous=task)

        return redirect(reverse("workbasket"))


@login_required
def ack_notification(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)
        application.check_expected_status([ImpExpStatus.COMPLETED])

        if request.method == "POST":
            task = application.get_expected_task(Task.TaskType.ACK, select_for_update=True)
            form = forms.AckReceiptForm(request.POST)

            if form.is_valid():
                application.acknowledged_by = request.user
                application.acknowledged_datetime = timezone.now()
                application.update_order_datetime()
                application.save()

                end_process_task(task)

                # TODO: ICMSLST-20
                # Notification is not cleared and still appear in the workbasket
                # It can be cleared with the generic 'Clear' feature in workbasket

                return redirect(
                    reverse(
                        "case:ack-notification",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = forms.AckReceiptForm()

        if case_type == "import":
            org = application.importer
        else:
            org = application.exporter

        context = {
            "process": application,
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "form": form,
            "primary_recipients": _get_primary_recipients(application),
            "copy_recipients": _get_copy_recipients(application),
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Response"),
            "acknowledged": application.acknowledged_by and application.acknowledged_datetime,
            "org": org,
            "show_generation_status": False,
            **get_document_context(application),
        }

        return render(
            request=request,
            template_name="web/domains/case/ack-notification.html",
            context=context,
        )


class ViewIssuedCaseDocumentsView(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, TemplateView
):
    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED]

    # TemplateView Config
    http_method_names = ["get"]
    template_name = "web/domains/case/view-case-documents.html"

    def has_permission(self):
        application = self.get_object().get_specific_model()

        try:
            check_application_permission(application, self.request.user, self.kwargs["case_type"])
        except PermissionDenied:
            return False

        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        application = self.application
        is_import_app = application.is_import_application()

        case_type = self.kwargs["case_type"]
        context["page_title"] = get_case_page_title(case_type, application, "Issued Documents")
        context["process_template"] = f"web/domains/case/{case_type}/partials/process.html"
        context["process"] = self.application
        context["primary_recipients"] = _get_primary_recipients(application)
        context["copy_recipients"] = _get_copy_recipients(application)
        context["case_type"] = case_type
        context["acknowledged"] = application.acknowledged_by and application.acknowledged_datetime
        context["org"] = application.importer if is_import_app else application.exporter
        issued_doc = self.application.get_issued_documents().get(
            pk=self.kwargs["issued_document_pk"]
        )
        context["issue_date"] = issued_doc.case_completion_datetime

        return context | get_document_context(self.application, issued_doc)


def _get_primary_recipients(application: ImpOrExp) -> "QuerySet[User]":
    if application.agent:
        return application.get_agent_contacts()
    else:
        return application.get_org_contacts()


def _get_copy_recipients(application: ImpOrExp) -> "QuerySet[User]":
    if application.agent:
        return application.get_org_contacts()
    else:
        return User.objects.none()
