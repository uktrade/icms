from typing import TYPE_CHECKING, Any, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View

from web.domains.case import forms
from web.domains.case.app_checks import get_app_errors
from web.domains.case.models import DocumentPackBase
from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.tasks import create_case_document_pack
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import end_process_task, get_case_page_title
from web.flow import errors
from web.models import CaseNote, Task, User, VariationRequest, WithdrawApplication
from web.notify.constants import DatabaseEmailTemplate, VariationRequestDescription
from web.notify.email import (
    send_database_email,
    send_reassign_email,
    send_refused_email,
    send_variation_request_email,
    send_withdrawal_email,
)
from web.permissions import (
    AppChecker,
    Perms,
    get_org_obj_permissions,
    organisation_get_contacts,
)
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import delete_file_from_s3, get_s3_client
from web.utils.validation import ApplicationErrors

from .mixins import ApplicationAndTaskRelatedObjectMixin, ApplicationTaskMixin
from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.case.types import DocumentPack


def check_can_edit_application(user: User, application: ImpOrExp) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


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

        check_can_edit_application(request.user, application)

        try:
            case_progress.check_expected_status(application, [ImpExpStatus.IN_PROGRESS])
            case_progress.check_expected_task(application, Task.TaskType.PREPARE)
        except errors.ProcessError:
            raise PermissionDenied

        application.delete()

        messages.success(request, "Application has been cancelled.")

        return redirect(reverse("workbasket"))


@login_required
def withdraw_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        """Applicant view for requesting an application is withdrawn.

        This can occur for initial applications or for variation requests.
        """

        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.check_expected_status(
            application,
            [ImpExpStatus.SUBMITTED, ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED],
        )

        if request.method == "POST":
            form = forms.WithdrawForm(request.POST)

            if form.is_valid():
                withdrawal = form.save(commit=False)

                if case_type == "import":
                    withdrawal.import_application = application
                elif case_type == "export":
                    withdrawal.export_application = application

                withdrawal.status = WithdrawApplication.Statuses.OPEN
                withdrawal.request_by = request.user
                withdrawal.save()

                application.update_order_datetime()
                application.save()

                messages.success(
                    request,
                    "You have requested that this application be withdrawn. Your request has been sent to ILB.",
                )
                send_withdrawal_email(withdrawal)

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        withdrawals = application.withdrawals.filter(is_active=True).order_by("-created_datetime")
        context = {
            "process": application,
            "page_title": get_case_page_title(case_type, application, "Withdrawals"),
            "form": form,
            "withdrawals": withdrawals,
            "previous_withdrawals": withdrawals.exclude(status="open"),
            "case_type": case_type,
        }
        return render(request, "web/domains/case/withdraw.html", context)


@login_required
@require_POST
def archive_withdrawal(
    request: AuthenticatedHttpRequest, *, application_pk: int, withdrawal_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        """Applicant view for retracting a withdrawal request.

        This can occur for initial applications or for variation requests.
        """

        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.check_expected_status(
            application,
            [ImpExpStatus.SUBMITTED, ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED],
        )

        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)
        withdrawal.status = WithdrawApplication.Statuses.DELETED
        withdrawal.is_active = False
        withdrawal.save()

        send_withdrawal_email(withdrawal)
        messages.success(
            request, "You have retracted your request for this application to be withdrawn."
        )

        return redirect(reverse("workbasket"))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_withdrawals(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """Management view for accepting or rejecting a withdrawal request."""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

        withdrawals = application.withdrawals.filter(is_active=True).order_by("-created_datetime")
        current_withdrawal = withdrawals.filter(status=WithdrawApplication.Statuses.OPEN).first()

        if request.method == "POST" and not readonly_view:
            task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

            form = forms.WithdrawResponseForm(request.POST, instance=current_withdrawal)

            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.response_by = request.user
                withdrawal.save()

                # withdrawal accepted - case is closed, else case still open
                if withdrawal.status == WithdrawApplication.Statuses.ACCEPTED:
                    if application.status == ImpExpStatus.VARIATION_REQUESTED:
                        application.status = ImpExpStatus.COMPLETED
                        # Close the open variation request if we are withdrawing the application / variation
                        vr = application.variation_requests.get(
                            status=VariationRequest.Statuses.OPEN
                        )
                        vr.status = VariationRequest.Statuses.WITHDRAWN
                        vr.reject_cancellation_reason = application.variation_refuse_reason
                        vr.closed_datetime = timezone.now()
                        vr.save()
                    else:
                        application.status = model_class.Statuses.WITHDRAWN
                        application.is_active = False

                    application.update_order_datetime()
                    application.save()

                    document_pack.pack_draft_archive(application)
                    end_process_task(task, request.user)
                    send_withdrawal_email(withdrawal)
                    return redirect(reverse("workbasket"))
                else:
                    send_withdrawal_email(withdrawal)
                    return redirect(
                        reverse(
                            "case:manage-withdrawals",
                            kwargs={"application_pk": application_pk, "case_type": case_type},
                        )
                    )
        else:
            form = forms.WithdrawResponseForm(instance=current_withdrawal)

        context = {
            "process": application,
            "page_title": get_case_page_title(case_type, application, "Withdrawals"),
            "form": form,
            "withdrawals": withdrawals,
            "current_withdrawal": current_withdrawal,
            "previous_withdrawals": withdrawals.exclude(status="open"),
            "case_type": case_type,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/withdrawals.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def take_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.check_expected_status(
            application, [ImpExpStatus.SUBMITTED, ImpExpStatus.VARIATION_REQUESTED]
        )
        case_progress.check_expected_task(application, Task.TaskType.PROCESS)

        if application.status == model_class.Statuses.SUBMITTED:
            application.status = model_class.Statuses.PROCESSING

            if case_type == "import":
                # Licence start date is set when ILB Admin takes the case
                licence = document_pack.pack_draft_get(application)

                if not licence.licence_start_date:
                    licence.licence_start_date = timezone.now().date()
                    licence.save()

        application.case_owner = request.user
        application.update_order_datetime()
        application.save()

        return redirect(
            reverse(
                "case:manage", kwargs={"application_pk": application.pk, "case_type": case_type}
            )
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def release_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if application.status != model_class.Statuses.VARIATION_REQUESTED:
            application.status = model_class.Statuses.SUBMITTED

        application.case_owner = None
        application.update_order_datetime()
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def reassign_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if application.is_import_application():
            form_class = forms.ReassignOwnershipImport
        else:
            form_class = forms.ReassignOwnershipExport

        if request.method == "POST":
            form = form_class(request.POST, instance=application)

            if form.is_valid():
                form.save(commit=False)
                application.reassign_datetime = timezone.now()
                application.save()

                comment = form.cleaned_data["comment"]

                if comment:
                    case_note = CaseNote.objects.create(created_by=request.user, note=comment)
                    application.case_notes.add(case_note)

                if form.cleaned_data["email_assignee"]:
                    send_reassign_email(application, comment)

                return redirect(reverse("workbasket"))

        else:
            form = form_class(instance=application)

        return render(
            request=request,
            template_name="web/domains/case/manage/reassign-ownership.html",
            context={"form": form, "case_type": case_type, "process": application},
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """Initial case management view for a case.

    Also used to stop an application.
    """

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

        if request.method == "POST" and not readonly_view:
            task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

            form = forms.CloseCaseForm(request.POST)

            if form.is_valid():
                application.status = model_class.Statuses.STOPPED
                application.save()
                end_process_task(task)

                document_pack.pack_draft_archive(application)

                if form.cleaned_data.get("send_email"):
                    send_database_email(application, DatabaseEmailTemplate.STOP_CASE)

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
            "page_title": get_case_page_title(case_type, application, "Manage"),
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request, template_name="web/domains/case/manage/manage.html", context=context
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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

        case_progress.application_in_processing(application)

        application_errors: ApplicationErrors = get_app_errors(application, case_type)

        if request.method == "POST" and not application_errors.has_errors():
            task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

            create_documents = True
            send_vr_email = False

            if application.status == application.Statuses.VARIATION_REQUESTED:
                if (
                    application.is_import_application()
                    and application.variation_decision == application.REFUSE
                ):
                    vr = application.variation_requests.get(status=VariationRequest.Statuses.OPEN)
                    next_task = None
                    application.status = model_class.Statuses.COMPLETED
                    vr.status = VariationRequest.Statuses.REJECTED
                    vr.reject_cancellation_reason = application.variation_refuse_reason
                    vr.closed_datetime = timezone.now()
                    vr.save()
                    send_vr_email = True
                    create_documents = False
                else:
                    next_task = Task.TaskType.AUTHORISE

            else:
                if application.decision == application.REFUSE:
                    next_task = Task.TaskType.REJECTED
                    application.status = model_class.Statuses.COMPLETED
                    create_documents = False

                else:
                    next_task = Task.TaskType.AUTHORISE
                    application.status = model_class.Statuses.PROCESSING

            application.update_order_datetime()
            application.save()

            end_process_task(task)

            if next_task:
                Task.objects.create(process=application, task_type=next_task, previous=task)

            if create_documents:
                document_pack.doc_ref_documents_create(application, request.icms.lock_manager)
            else:
                document_pack.pack_draft_archive(application)

            if (
                application.decision == application.REFUSE
                and application.status == model_class.Statuses.COMPLETED
            ):
                send_refused_email(application)

            if send_vr_email:
                send_variation_request_email(vr, VariationRequestDescription.REFUSED, application)
            return redirect(reverse("workbasket"))

        else:
            context = {
                "case_type": case_type,
                "process": application,
                "page_title": get_case_page_title(case_type, application, "Authorisation"),
                "errors": application_errors if application_errors.has_errors() else None,
            }

            return render(
                request=request,
                template_name="web/domains/case/authorisation.html",
                context=context,
            )


@login_required
@sensitive_post_parameters("password")
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def authorise_documents(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_is_authorised(application)
        task = case_progress.get_expected_task(application, Task.TaskType.AUTHORISE)

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
            "case_type": case_type,
            "process": application,
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
    permission_required = [Perms.sys.ilb_admin]

    def get(self, request: HttpRequest, *args, **kwargs) -> Any:
        self.set_application_and_task()

        active_tasks = case_progress.get_active_task_list(self.application)

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
    permission_required = [Perms.sys.ilb_admin]

    def post(self, request: HttpRequest, *args, **kwargs) -> Any:
        """Deletes existing draft PDFs and regenerates case document pack"""
        self.set_application_and_task()
        doc_pack = document_pack.pack_draft_get(self.application)
        documents = document_pack.doc_ref_documents_all(doc_pack)

        s3_client = get_s3_client()
        for cdr in documents:
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def view_document_packs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """ILB Admin view to view the application documents before authorising."""

    with transaction.atomic():
        model_class = get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_is_authorised(application)

        context = {
            "case_type": case_type,
            "process": application,
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
    issued_document: Optional["DocumentPack"] = None,
) -> dict[str, str]:
    at = application.application_type

    if application.is_import_application():
        # A supplied document pack or the current draft pack
        licence = issued_document or document_pack.pack_draft_get(application)

        licence_doc = document_pack.doc_ref_licence_get(licence)
        cover_letter = document_pack.doc_ref_cover_letter_get(licence)

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
                "case:cover-letter-pre-sign",
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
        # A supplied document pack or the current draft pack
        certificate = issued_document or document_pack.pack_draft_get(application)

        certificate_docs = document_pack.doc_ref_certificates_all(certificate)
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def cancel_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_is_authorised(application)
        task = case_progress.get_expected_task(application, Task.TaskType.AUTHORISE)

        if application.status != model_class.Statuses.VARIATION_REQUESTED:
            application.status = model_class.Statuses.PROCESSING

        application.update_order_datetime()
        application.save()

        end_process_task(task, request.user)

        Task.objects.create(process=application, task_type=Task.TaskType.PROCESS, previous=task)

        return redirect(reverse("workbasket"))


class ViewIssuedCaseDocumentsView(ApplicationTaskMixin, LoginRequiredMixin, TemplateView):
    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED]

    # TemplateView Config
    http_method_names = ["get"]
    template_name = "web/domains/case/view-case-documents.html"

    def has_object_permission(self) -> bool:
        return AppChecker(self.request.user, self.application).can_view()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        application = self.application
        is_import_app = application.is_import_application()

        case_type = self.kwargs["case_type"]
        context["page_title"] = get_case_page_title(case_type, application, "Issued Documents")
        context["process"] = self.application
        context["primary_recipients"] = _get_primary_recipients(application)
        context["copy_recipients"] = _get_copy_recipients(application)
        context["case_type"] = case_type
        context["org"] = application.importer if is_import_app else application.exporter

        issued_documents = document_pack.pack_issued_get_all(self.application)

        issued_doc = issued_documents.get(pk=self.kwargs["issued_document_pk"])
        context["issue_date"] = issued_doc.case_completion_datetime

        return context | get_document_context(self.application, issued_doc)


@method_decorator(transaction.atomic, name="post")
class ClearIssuedCaseDocumentsFromWorkbasket(
    ApplicationAndTaskRelatedObjectMixin, LoginRequiredMixin, View
):
    # ApplicationAndTaskRelatedObjectMixin Config
    current_status = [ImpExpStatus.COMPLETED]

    # View Config
    http_method_names = ["post"]

    def has_object_permission(self) -> bool:
        return AppChecker(self.request.user, self.application).can_view()

    def post(self, request: HttpRequest, *args, **kwargs) -> Any:
        """Remove the document pack from the workbasket."""
        self.set_application_and_task()

        pack_pk = self.kwargs["issued_document_pk"]

        try:
            document_pack.pack_workbasket_remove_pack(
                self.application, request.user, pack_pk=pack_pk
            )
        except ObjectDoesNotExist:
            raise Http404("No %s matches the given query." % DocumentPackBase._meta.object_name)

        self.update_application_tasks()

        return redirect(reverse("workbasket"))


@method_decorator(transaction.atomic, name="post")
class ClearCaseFromWorkbasket(ApplicationTaskMixin, LoginRequiredMixin, View):
    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED, ImpExpStatus.REVOKED]

    # View Config
    http_method_names = ["post"]

    def has_object_permission(self) -> bool:
        return AppChecker(self.request.user, self.application).can_view()

    def post(self, request: HttpRequest, *args, **kwargs) -> Any:
        """Remove the Case from the `request.user` workbasket."""

        self.set_application_and_task()

        self.application.cleared_by.add(self.request.user)

        if self.kwargs["case_type"] == "import":
            view_name = "Search Import Applications"
        else:
            view_name = "Search Certificate Applications"

        messages.success(request, f"Case cleared, it can still be viewed in the {view_name} page.")

        return redirect(reverse("workbasket"))


def _get_primary_recipients(application: ImpOrExp) -> "QuerySet[User]":
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter

    obj_perms = get_org_obj_permissions(org)
    users = organisation_get_contacts(org, perms=[obj_perms.edit.codename])

    return users


def _get_copy_recipients(application: ImpOrExp) -> "QuerySet[User]":
    if application.agent:
        # if agent return main org contacts
        org = application.agent.get_main_org()

        obj_perms = get_org_obj_permissions(org)
        return organisation_get_contacts(org, perms=[obj_perms.edit.codename])

    else:
        return User.objects.none()
