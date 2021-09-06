from typing import TYPE_CHECKING, Any, NamedTuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST
from guardian.shortcuts import get_users_with_perms

from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.opt.forms import FurtherQuestionsBaseOPTForm
from web.domains.case._import.opt.utils import get_fq_form, get_fq_page_name
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CFSProduct,
    CFSSchedule,
)
from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.file.utils import create_file_model
from web.domains.sanction_email.models import SanctionEmail
from web.domains.template.models import Template
from web.domains.user.models import User
from web.flow.models import Task
from web.models import (
    AccessRequest,
    CertificateOfManufactureApplication,
    CommodityGroup,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ExportApplicationType,
    ExporterAccessRequest,
    GMPFile,
    ImportApplication,
    ImporterAccessRequest,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    OutwardProcessingTradeFile,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    WithdrawApplication,
    WoodQuotaApplication,
)
from web.notify import email, notify
from web.notify.email import send_email
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import annotate_commodity_unit
from web.utils.s3 import get_file_from_s3, get_s3_client
from web.utils.validation import ApplicationErrors

from . import forms, models
from .app_checks import get_app_errors
from .fir import forms as fir_forms
from .fir.models import FurtherInformationRequest
from .types import (
    ApplicationsWithCaseEmail,
    CaseEmailConfig,
    ImpOrExp,
    ImpOrExpOrAccess,
    ImpOrExpOrAccessT,
    ImpOrExpT,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet


def _get_class_imp_or_exp(case_type: str) -> ImpOrExpT:
    if case_type == "import":
        return ImportApplication
    elif case_type == "export":
        return ExportApplication
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def _get_class_imp_or_exp_or_access(case_type: str) -> ImpOrExpOrAccessT:
    if case_type == "import":
        return ImportApplication
    elif case_type == "export":
        return ExportApplication
    elif case_type == "access":
        return AccessRequest
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def _has_importer_exporter_access(user: User, case_type: str) -> bool:
    if case_type == "import":
        return user.has_perm("web.importer_access")
    elif case_type == "export":
        return user.has_perm("web.exporter_access")

    raise NotImplementedError(f"Unknown case_type {case_type}")


def check_application_permission(application: ImpOrExpOrAccess, user: User, case_type: str) -> None:
    """Check the given user has permission to access the given application."""

    if user.has_perm("web.reference_data_access"):
        return

    if case_type == "access":
        if user != application.submitted_by:
            raise PermissionDenied

    elif case_type in ["import", "export"]:
        assert isinstance(application, (ImportApplication, ExportApplication))

        if not _has_importer_exporter_access(user, case_type):
            raise PermissionDenied

        is_contact = application.user_is_contact_of_org(user)
        is_agent = application.user_is_agent_of_org(user)

        if not is_contact and not is_agent:
            raise PermissionDenied

    else:
        # Should never get here.
        raise PermissionDenied


def get_application_current_task(
    application: ImpOrExpOrAccess, case_type: str, task_type: str
) -> Task:
    """Gets the current valid task for all application types.

    Also ensure the application is in the correct status for the supplied task.
    """

    if case_type in ["import", "export"]:
        if task_type == Task.TaskType.PROCESS:
            return application.get_task(
                [application.Statuses.SUBMITTED, application.Statuses.WITHDRAWN], task_type
            )
        elif task_type == Task.TaskType.PREPARE:
            return application.get_task(
                [application.Statuses.IN_PROGRESS, application.Statuses.UPDATE_REQUESTED], task_type
            )
        elif task_type == Task.TaskType.AUTHORISE:
            return application.get_task(application.Statuses.PROCESSING, task_type)
    elif case_type == "access":
        if task_type == Task.TaskType.PROCESS:
            return application.get_task(application.Statuses.SUBMITTED, task_type)

    raise NotImplementedError(
        f"State not supported for app: '{application.process_type}', case type: '{case_type}'"
        f" and task type: '{task_type}'."
    )


class OPTFurtherQuestionsSharedSection(NamedTuple):
    form: FurtherQuestionsBaseOPTForm
    section_title: str
    supporting_documents: "QuerySet[OutwardProcessingTradeFile]"


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def list_notes(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        context = {
            "process": application,
            "notes": application.case_notes,
            "case_type": case_type,
            "page_title": get_page_title(case_type, application, "Notes"),
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/list-notes.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def add_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application.case_notes.create(status=models.CASE_NOTE_DRAFT, created_by=request.user)

    return redirect(
        reverse(
            "case:list-notes", kwargs={"application_pk": application_pk, "case_type": case_type}
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application.case_notes.filter(pk=note_pk).update(is_active=False)

    return redirect(
        reverse(
            "case:list-notes", kwargs={"application_pk": application_pk, "case_type": case_type}
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application.case_notes.filter(pk=note_pk).update(is_active=True)

    return redirect(
        reverse(
            "case:list-notes", kwargs={"application_pk": application_pk, "case_type": case_type}
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        note = application.case_notes.get(pk=note_pk)

        if not note.is_active:
            messages.error(request, "Editing of deleted notes is not allowed.")

            return redirect(
                reverse(
                    "case:list-notes",
                    kwargs={"application_pk": application_pk, "case_type": case_type},
                )
            )

        if request.POST:
            note_form = forms.CaseNoteForm(request.POST, instance=note)

            if note_form.is_valid():
                note_form.save()

                return redirect(
                    reverse(
                        "case:edit-note",
                        kwargs={
                            "application_pk": application_pk,
                            "note_pk": note_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            note_form = forms.CaseNoteForm(instance=note)

        context = {
            "process": application,
            "note_form": note_form,
            "note": note,
            "case_type": case_type,
            "page_title": get_page_title(case_type, application, "Edit Note"),
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/edit-note.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_note_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    note_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        note = application.case_notes.get(pk=note_pk)

        if request.POST:
            form = forms.DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, note.files)

                return redirect(
                    reverse(
                        "case:edit-note",
                        kwargs={
                            "application_pk": application_pk,
                            "note_pk": note_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            form = forms.DocumentForm()

        context = {
            "process": application,
            "form": form,
            "note": note,
            "case_type": case_type,
            "page_title": get_page_title(case_type, application, "Add Note"),
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/add-note-document.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def view_note_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    note_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    application: ImpOrExp = get_object_or_404(model_class, pk=application_pk)  # type: ignore[assignment]
    note = application.case_notes.get(pk=note_pk)
    document = note.files.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_note_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    note_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        document = application.case_notes.get(pk=note_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            "case:edit-note",
            kwargs={"application_pk": application_pk, "note_pk": note_pk, "case_type": case_type},
        )
    )


# "Applicant Case Management" Views
@login_required
def withdraw_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
            form = forms.WithdrawForm(request.POST)

            if form.is_valid():
                withdrawal = form.save(commit=False)

                if case_type == "import":
                    withdrawal.import_application = application
                elif case_type == "export":
                    withdrawal.export_application = application

                withdrawal.request_by = request.user
                withdrawal.save()

                application.status = model_class.Statuses.WITHDRAWN
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(
                    process=application, task_type=Task.TaskType.PROCESS, previous=task
                )

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "process": application,
            "task": task,
            "page_title": get_page_title(case_type, application, "Withdrawals"),
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
        model_class = _get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)

        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application.status = model_class.Statuses.SUBMITTED
        application.save()

        withdrawal.is_active = False
        withdrawal.save()

        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=application, task_type=Task.TaskType.PROCESS, previous=task)

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_update_requests(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if case_type == "import":
            template_code = "IMA_APP_UPDATE"

            placeholder_content = {
                "CASE_REFERENCE": application.reference,
                "IMPORTER_NAME": application.importer.display_name,
                "CASE_OFFICER_NAME": request.user,
            }
        elif case_type == "export":
            template_code = "CA_APPLICATION_UPDATE_EMAIL"

            placeholder_content = {
                "CASE_REFERENCE": application.reference,
                "EXPORTER_NAME": application.exporter.name,
                "CASE_OFFICER_NAME": request.user,
            }
        else:
            raise NotImplementedError(
                f"case type {case_type} is not implemented for update requests"
            )

        template = Template.objects.get(template_code=template_code, is_active=True)
        email_subject = template.get_title({"CASE_REFERENCE": application.reference})
        email_content = template.get_content(placeholder_content)

        if request.POST:
            form = forms.UpdateRequestForm(request.POST)
            if form.is_valid():
                update_request = form.save(commit=False)
                update_request.requested_by = request.user
                update_request.request_datetime = timezone.now()
                update_request.status = models.UpdateRequest.Status.OPEN
                update_request.save()

                application.status = model_class.Statuses.UPDATE_REQUESTED
                application.save()
                application.update_requests.add(update_request)

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(
                    process=application, task_type=Task.TaskType.PREPARE, previous=task
                )

                if case_type == "import":
                    contacts = get_users_with_perms(
                        application.importer, only_with_perms_in=["is_contact_of_importer"]
                    ).filter(user_permissions__codename="importer_access")
                elif case_type == "export":
                    contacts = get_users_with_perms(
                        application.exporter, only_with_perms_in=["is_contact_of_exporter"]
                    ).filter(user_permissions__codename="exporter_access")
                else:
                    raise NotImplementedError(
                        f"case type {case_type} is not implemented for update requests"
                    )

                recipients = list(contacts.values_list("email", flat=True))

                email.send_email.delay(
                    update_request.request_subject,
                    update_request.request_detail,
                    recipients,
                    update_request.email_cc_address_list,
                )

                return redirect(reverse("workbasket"))
        else:
            form = forms.UpdateRequestForm(
                initial={
                    "request_subject": email_subject,
                    "request_detail": email_content,
                }
            )

        update_requests = application.update_requests.filter(is_active=True)
        update_request = update_requests.filter(
            status__in=[models.UpdateRequest.Status.OPEN, models.UpdateRequest.Status.RESPONDED]
        ).first()
        previous_update_requests = update_requests.filter(status=models.UpdateRequest.Status.CLOSED)

        context = {
            "process": application,
            "task": task,
            "page_title": get_page_title(case_type, application, "Update Requests"),
            "form": form,
            "previous_update_requests": previous_update_requests,
            "update_request": update_request,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/update-requests.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def close_update_request(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    update_request_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        update_request = get_object_or_404(application.update_requests, pk=update_request_pk)

        update_request.status = models.UpdateRequest.Status.CLOSED
        update_request.closed_by = request.user
        update_request.closed_datetime = timezone.now()
        update_request.save()

    return redirect(
        reverse(
            "case:manage-update-requests",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
    )


@login_required
def start_update_request(
    request: AuthenticatedHttpRequest, *, application_pk: int, update_request_pk=int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)

        get_application_current_task(application, case_type, Task.TaskType.PREPARE)

        update_requests = application.update_requests.filter(is_active=True)
        update_request = get_object_or_404(
            update_requests.filter(is_active=True).filter(status=models.UpdateRequest.Status.OPEN),
            pk=update_request_pk,
        )
        previous_update_requests = update_requests.filter(status=models.UpdateRequest.Status.CLOSED)

        if request.POST:
            update_request.status = models.UpdateRequest.Status.UPDATE_IN_PROGRESS
            update_request.save()

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application_pk})
            )

        context = {
            "process": application,
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "update_request": update_request,
            "previous_update_requests": previous_update_requests,
        }

        return render(
            request=request,
            template_name="web/domains/case/start-update-request.html",
            context=context,
        )


@login_required
def respond_update_request(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, case_type)

        get_application_current_task(application, case_type, Task.TaskType.PREPARE)

        update_requests = application.update_requests.filter(is_active=True)
        update_request = update_requests.get(
            status__in=[
                models.UpdateRequest.Status.UPDATE_IN_PROGRESS,
                models.UpdateRequest.Status.RESPONDED,
            ]
        )
        previous_update_requests = update_requests.filter(status=models.UpdateRequest.Status.CLOSED)

        if request.POST:
            form = forms.UpdateRequestResponseForm(request.POST, instance=update_request)
            if form.is_valid():
                update_request = form.save(commit=False)
                update_request.status = models.UpdateRequest.Status.RESPONDED

                update_request.response_by = request.user
                update_request.response_datetime = timezone.now()
                update_request.save()

                return redirect(
                    reverse(
                        application.get_edit_view_name(), kwargs={"application_pk": application_pk}
                    )
                )
        else:
            form = forms.UpdateRequestResponseForm(instance=update_request)

        context = {
            "process": application,
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "form": form,
            "update_request": update_request,
            "previous_update_requests": previous_update_requests,
        }

        return render(
            request=request,
            template_name="web/domains/case/respond-update-request.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if case_type in ["import", "export"]:
            show_firs = True

        elif case_type == "access":
            if application.process_type == "ImporterAccessRequest":
                show_firs = application.importeraccessrequest.link_id  # type: ignore[union-attr]
            else:
                show_firs = application.exporteraccessrequest.link_id  # type: ignore[union-attr]
        else:
            raise NotImplementedError(f"Unknown case_type {case_type}")

        extra_context = {"show_firs": show_firs}

        context = {
            "process": application,
            "task": task,
            "firs": application.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ),
            "case_type": case_type,
            "page_title": get_page_title(case_type, application, "Further Information Requests"),
            **extra_context,
        }
    return render(
        request=request,
        template_name="web/domains/case/manage/list-firs.html",
        context=context,
    )


def _manage_fir_redirect(application_pk: int, case_type: str) -> HttpResponse:
    return redirect(
        reverse(
            "case:manage-firs",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def add_fir(request, *, application_pk: int, case_type: str) -> HttpResponse:
    model_class = _get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        template = Template.objects.get(template_code="IAR_RFI_EMAIL", is_active=True)
        title_mapping = {"REQUEST_REFERENCE": application.reference}
        content_mapping = {
            "REQUESTER_NAME": application.submitted_by,
            "CURRENT_USER_NAME": request.user,
            "REQUEST_REFERENCE": application.pk,
        }

        application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=template.get_title(title_mapping),
            request_detail=template.get_content(content_mapping),
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_fir(request, *, application_pk: int, fir_pk: int, case_type: str) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        if case_type == "access":
            contacts = [application.submitted_by]

        elif case_type == "import":
            contacts = get_users_with_perms(
                application.importer, only_with_perms_in=["is_contact_of_importer"]
            ).filter(user_permissions__codename="importer_access")

        elif case_type == "export":
            contacts = get_users_with_perms(
                application.exporter, only_with_perms_in=["is_contact_of_exporter"]
            ).filter(user_permissions__codename="exporter_access")

        else:
            raise NotImplementedError(f"Unknown case_type {case_type}")

        fir = get_object_or_404(application.further_information_requests.draft(), pk=fir_pk)

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
            form = fir_forms.FurtherInformationRequestForm(request.POST, instance=fir)

            if form.is_valid():
                fir = form.save()

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()
                    notify.further_information_requested(fir, contacts)

                return _manage_fir_redirect(application_pk, case_type)
        else:
            form = fir_forms.FurtherInformationRequestForm(instance=fir)

        context = {
            "process": application,
            "task": task,
            "form": form,
            "fir": fir,
            "case_type": case_type,
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/edit-fir.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        fir.is_active = False
        fir.status = FurtherInformationRequest.DELETED
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def withdraw_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def close_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_fir_file(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    redirect_url = "case:edit-fir"
    template_name = "web/domains/case/fir/add-fir-file.html"

    return _add_fir_file(request, application_pk, fir_pk, case_type, redirect_url, template_name)


@login_required
def add_fir_response_file(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    redirect_url = "case:respond-fir"
    template_name = "web/domains/case/fir/add-fir-response-file.html"

    return _add_fir_file(request, application_pk, fir_pk, case_type, redirect_url, template_name)


def _add_fir_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    case_type: str,
    redirect_url: str,
    template_name: str,
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)
        check_application_permission(application, request.user, case_type)

        fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

        if request.POST:
            form = forms.DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, fir.files)

                return redirect(
                    reverse(
                        redirect_url,
                        kwargs={
                            "application_pk": application_pk,
                            "fir_pk": fir_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            form = forms.DocumentForm()

        context = {
            "process": application,
            "form": form,
            "fir": fir,
            "case_type": case_type,
            "prev_link": redirect_url,
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
        }

    return render(
        request=request,
        template_name=template_name,
        context=context,
    )


@login_required
@require_GET
def view_fir_file(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:

    model_class = _get_class_imp_or_exp_or_access(case_type)
    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)
    fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

    return view_application_file(request.user, application, fir.files, file_pk, case_type)


def view_application_file(
    user: User,
    application: ImpOrExpOrAccess,
    related_file_model: Any,
    file_pk: int,
    case_type: str,
) -> HttpResponse:

    check_application_permission(application, user, case_type)

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


def view_application_file_direct(
    user: User,
    application: ImpOrExpOrAccess,
    document: File,
    case_type: str,
) -> HttpResponse:

    check_application_permission(application, user, case_type)

    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_fir_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:
    redirect_url = "case:edit-fir"

    return _delete_fir_file(request.user, application_pk, fir_pk, file_pk, case_type, redirect_url)


@login_required
@require_POST
def delete_fir_response_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: str,
):
    redirect_url = "case:respond-fir"

    return _delete_fir_file(request.user, application_pk, fir_pk, file_pk, case_type, redirect_url)


def _delete_fir_file(
    user: User, application_pk: int, fir_pk: int, file_pk: int, case_type: str, redirect_url: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, user, case_type)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        document = application.further_information_requests.get(pk=fir_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            redirect_url,
            kwargs={"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type},
        )
    )


@login_required
def list_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, case_type)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

    context = {
        "process": application,
        "process_template": f"web/domains/case/{case_type}/partials/process.html",
        "firs": application.further_information_requests.filter(
            Q(status=FurtherInformationRequest.OPEN)
            | Q(status=FurtherInformationRequest.RESPONDED)
            | Q(status=FurtherInformationRequest.CLOSED)
        ),
        "case_type": case_type,
    }

    return render(request, "web/domains/case/list-firs.html", context)


@login_required
def respond_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:

    with transaction.atomic():
        model_class = _get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, case_type)

        fir = get_object_or_404(application.further_information_requests.open(), pk=fir_pk)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir, data=request.POST)

            if form.is_valid():
                fir = form.save()

                fir.response_datetime = timezone.now()
                fir.status = FurtherInformationRequest.RESPONDED
                fir.response_by = request.user
                fir.save()

                notify.further_information_responded(application, fir)

                return redirect(reverse("workbasket"))
        else:
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir)

    context = {
        "process": application,
        "process_template": f"web/domains/case/{case_type}/partials/process.html",
        "fir": fir,
        "form": form,
        "case_type": case_type,
    }

    return render(request, "web/domains/case/respond-fir.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_withdrawals(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        withdrawals = application.withdrawals.filter(is_active=True)
        current_withdrawal = withdrawals.filter(status=WithdrawApplication.STATUS_OPEN).first()

        if request.POST:
            form = forms.WithdrawResponseForm(request.POST, instance=current_withdrawal)

            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.response_by = request.user
                withdrawal.save()

                # withdrawal accepted - case is closed, else case still open
                if withdrawal.status == WithdrawApplication.STATUS_ACCEPTED:
                    application.is_active = False
                    application.save()

                    task.is_active = False
                    task.finished = timezone.now()
                    task.save()

                    return redirect(reverse("workbasket"))
                else:
                    application.status = model_class.Statuses.SUBMITTED
                    application.save()

                    task.is_active = False
                    task.finished = timezone.now()
                    task.save()

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
            "page_title": get_page_title(case_type, application, "Withdrawals"),
            "form": form,
            "withdrawals": withdrawals,
            "current_withdrawal": current_withdrawal,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/withdrawals.html",
            context=context,
        )


@login_required
def view_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp_or_access(case_type)
    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)

    check_application_permission(application, request.user, case_type)

    # Access Requests
    if application.process_type == ImporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.importeraccessrequest)  # type: ignore[union-attr]

    elif application.process_type == ExporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.exporteraccessrequest)  # type: ignore[union-attr]

    # Import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _view_fa_oil(request, application.openindividuallicenceapplication)  # type: ignore[union-attr]

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return _view_fa_sil(request, application.silapplication)  # type: ignore[union-attr]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _view_sanctions_and_adhoc(request, application.sanctionsandadhocapplication)  # type: ignore[union-attr]

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _view_wood_quota(request, application.woodquotaapplication)  # type: ignore[union-attr]

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _view_derogations(request, application.derogationsapplication)  # type: ignore[union-attr]

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return _view_dfl(request, application.dflapplication)  # type: ignore[union-attr]

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        return _view_opt(request, application.outwardprocessingtradeapplication)  # type: ignore[union-attr]

    elif application.process_type == TextilesApplication.PROCESS_TYPE:
        return _view_textiles_quota(request, application.textilesapplication)  # type: ignore[union-attr]

    elif application.process_type == PriorSurveillanceApplication.PROCESS_TYPE:
        return _view_sps(request, application.priorsurveillanceapplication)  # type: ignore[union-attr]

    elif application.process_type == IronSteelApplication.PROCESS_TYPE:
        return _view_ironsteel(request, application.ironsteelapplication)  # type: ignore[union-attr]

    # Export applications
    elif application.process_type == CertificateOfManufactureApplication.PROCESS_TYPE:
        return _view_com(request, application.certificateofmanufactureapplication)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return _view_cfs(request, application.certificateoffreesaleapplication)

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return _view_gmp(request, application.certificateofgoodmanufacturingpracticeapplication)

    else:
        raise NotImplementedError(f"Unknown process_type {application.process_type}")


def _view_fa_oil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-oil/view.html", context)


def _view_fa_sil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "verified_section5": application.importer.section5_authorities.currently_active(),
        "user_section5": application.user_section5.filter(is_active=True),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-sil/view.html", context)


def _view_sanctions_and_adhoc(
    request: AuthenticatedHttpRequest, application: SanctionsAndAdhocApplication
) -> HttpResponse:

    goods = annotate_commodity_unit(
        application.sanctionsandadhocapplicationgoods_set.all(), "commodity__"
    ).distinct()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "goods": goods,
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/sanctions/view.html", context)


def _view_wood_quota(
    request: AuthenticatedHttpRequest, application: WoodQuotaApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "contract_documents": application.contract_documents.filter(is_active=True),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/wood/view.html", context)


def _view_derogations(
    request: AuthenticatedHttpRequest, application: DerogationsApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/derogations/view.html", context)


def _view_dfl(request: AuthenticatedHttpRequest, application: DFLApplication) -> HttpResponse:
    goods_list = application.goods_certificates.filter(is_active=True).select_related(
        "issuing_country"
    )
    contact_list = application.importcontact_set.all()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "goods_list": goods_list,
        "contacts": contact_list,
    }

    return render(request, "web/domains/case/import/fa-dfl/view.html", context)


def _view_opt(
    request: AuthenticatedHttpRequest, application: OutwardProcessingTradeApplication
) -> HttpResponse:
    group = CommodityGroup.objects.get(
        commodity_type__type_code="TEXTILES", group_code=application.cp_category
    )
    category_group_description = group.group_description

    # Reuse the model verbose_name for the labels
    opt_fields = OutwardProcessingTradeApplication._meta.get_fields()
    labels = {f.name: getattr(f, "verbose_name", "") for f in opt_fields}

    # Reuse the forms to render the different further questions sections
    # key=section name, value=template context
    fq_sections: dict[str, OPTFurtherQuestionsSharedSection] = {}

    for file_type in OutwardProcessingTradeFile.Type:  # type: ignore[attr-defined]
        if file_type != OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT:
            form_class = get_fq_form(file_type)
            section_title = get_fq_page_name(file_type)

            form = form_class(instance=application, has_files=False)
            supporting_documents = application.documents.filter(is_active=True, file_type=file_type)

            fq_sections[file_type] = OPTFurtherQuestionsSharedSection(
                form=form, section_title=section_title, supporting_documents=supporting_documents
            )

    # Supporting docs for the main form:
    supporting_documents = application.documents.filter(
        is_active=True, file_type=OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT
    )

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "category_group_description": category_group_description,
        "labels": labels,
        "fq_sections": fq_sections,
        "supporting_documents": supporting_documents,
    }

    return render(request, "web/domains/case/import/opt/view.html", context)


def _view_textiles_quota(
    request: AuthenticatedHttpRequest, application: TextilesApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/textiles/view.html", context)


def _view_sps(
    request: AuthenticatedHttpRequest, application: PriorSurveillanceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/sps/view.html", context)


def _view_ironsteel(
    request: AuthenticatedHttpRequest, application: IronSteelApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
        "certificates": application.certificates.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/ironsteel/view.html", context)


def _view_accessrequest(
    request: AuthenticatedHttpRequest, application: AccessRequest
) -> HttpResponse:
    context = {"process": application, "page_title": get_page_title("access", application, "View")}

    return render(request, "web/domains/case/access/case-view.html", context)


def _view_com(
    request: AuthenticatedHttpRequest, application: CertificateOfManufactureApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "page_title": get_page_title("export", application, "View"),
    }

    return render(request, "web/domains/case/export/com/view.html", context)


def _view_cfs(request: AuthenticatedHttpRequest, application: CertificateOfFreeSaleApplication):

    # Reuse the model verbose_name for the labels
    cfs_fields = CFSSchedule._meta.get_fields()
    labels = {f.name: getattr(f, "verbose_name", "") for f in cfs_fields}
    app_countries = "\n".join(application.countries.all().values_list("name", flat=True))

    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "labels": labels,
        "application_countries": app_countries,
        "schedules": application.schedules.filter(is_active=True).order_by("created_at"),
        "page_title": get_page_title("export", application, "View"),
    }

    return render(request, "web/domains/case/export/cfs-view.html", context)


def _view_gmp(
    request: AuthenticatedHttpRequest,
    application: CertificateOfGoodManufacturingPracticeApplication,
) -> HttpResponse:
    show_iso_table = application.gmp_certificate_issued == application.CertificateTypes.ISO_22716
    show_brc_table = application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP

    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "page_title": get_page_title("export", application, "View"),
        "country": application.countries.first(),
        "show_iso_table": show_iso_table,
        "show_brc_table": show_brc_table,
        "GMPFileTypes": GMPFile.Type,
    }

    return render(request, "web/domains/case/export/gmp-view.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def take_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PROCESS)

        application.case_owner = request.user

        if case_type == "import":
            # Licence start date is set when ILB Admin takes the case
            application.licence_start_date = timezone.now().date()

        application.save()

        return redirect(
            reverse(
                "case:manage", kwargs={"application_pk": application.pk, "case_type": case_type}
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def release_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application.case_owner = None
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
            form = forms.CloseCaseForm(request.POST)

            if form.is_valid():
                application.status = model_class.Statuses.STOPPED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

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

                return redirect(reverse("workbasket"))
        else:
            form = forms.CloseCaseForm()

        context = {
            "case_type": case_type,
            "process": application,
            "task": task,
            "page_title": get_page_title(case_type, application, "Manage"),
            "form": form,
        }

        return render(
            request=request, template_name="web/domains/case/manage/manage.html", context=context
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def prepare_response(
    request: AuthenticatedHttpRequest, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    if case_type == "import":
        form_class = forms.ResponsePreparationImportForm
    elif case_type == "export":
        form_class = forms.ResponsePreparationExportForm
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
            form = form_class(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = form_class()

        if case_type == "import":
            cover_letter_flag = application.application_type.cover_letter_flag
            electronic_licence_flag = application.application_type.electronic_licence_flag
            endorsements_flag = application.application_type.endorsements_flag
        else:
            cover_letter_flag = False
            electronic_licence_flag = False
            endorsements_flag = False

        context = {
            "case_type": case_type,
            "task": task,
            "page_title": get_page_title(case_type, application, "Response Preparation"),
            "form": form,
            "cover_letter_flag": cover_letter_flag,
            "electronic_licence_flag": electronic_licence_flag,
            # Not used currently but the template probably should.
            # Once the data is confirmed to be correct
            "endorsements_flag": endorsements_flag,
        }

    # Import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _prepare_fa_oil_response(
            request, application.openindividuallicenceapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return _prepare_fa_dfl_response(request, application.dflapplication, context)  # type: ignore[union-attr]

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return _prepare_fa_sil_response(request, application.silapplication, context)  # type: ignore[union-attr]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _prepare_sanctions_and_adhoc_response(
            request, application.sanctionsandadhocapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _prepare_derogations_response(request, application.derogationsapplication, context)  # type: ignore[union-attr]

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _prepare_wood_quota_response(request, application.woodquotaapplication, context)  # type: ignore[union-attr]

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        return _prepare_opt_response(
            request, application.outwardprocessingtradeapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == TextilesApplication.PROCESS_TYPE:
        return _prepare_textiles_quota_response(request, application.textilesapplication, context)  # type: ignore[union-attr]

    elif application.process_type == PriorSurveillanceApplication.PROCESS_TYPE:
        return _prepare_sps_response(request, application.priorsurveillanceapplication, context)  # type: ignore[union-attr]

    elif application.process_type == IronSteelApplication.PROCESS_TYPE:
        return _prepare_ironsteel_response(request, application.ironsteelapplication, context)  # type: ignore[union-attr]

    # Certificate applications
    elif application.process_type == CertificateOfManufactureApplication.PROCESS_TYPE:
        return _prepare_com_response(request, application.certificateofmanufactureapplication, context)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return _prepare_cfs_response(request, application.certificateoffreesaleapplication, context)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return _prepare_gmp_response(
            request, application.certificateofgoodmanufacturingpracticeapplication, context  # type: ignore[union-attr]
        )

    else:
        raise NotImplementedError(
            f"Application process type '{application.process_type}' haven't been configured yet"
        )


def _prepare_fa_oil_response(
    request: AuthenticatedHttpRequest,
    application: OpenIndividualLicenceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-oil-response.html",
        context=context,
    )


def _prepare_fa_dfl_response(
    request: AuthenticatedHttpRequest, application: DFLApplication, context: dict[str, Any]
):
    context.update(
        {
            "process": application,
            "goods": application.goods_certificates.all().filter(is_active=True),
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-dfl-response.html",
        context=context,
    )


def _prepare_fa_sil_response(
    request: AuthenticatedHttpRequest, application: SILApplication, context: dict[str, Any]
):
    section_1 = application.goods_section1.filter(is_active=True)
    section_2 = application.goods_section2.filter(is_active=True)
    section_5 = application.goods_section5.filter(is_active=True)
    section_58 = application.goods_section582_obsoletes.filter(is_active=True)
    section_58_other = application.goods_section582_others.filter(is_active=True)

    has_goods = any(
        (s.exists() for s in (section_1, section_2, section_5, section_58, section_58_other))
    )

    context.update(
        {
            "process": application,
            "has_goods": has_goods,
            "goods_section_1": section_1,
            "goods_section_2": section_2,
            "goods_section_5": section_5,
            "goods_section_58": section_58,
            "goods_section_58_other": section_58_other,
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-sil-response.html",
        context=context,
    )


def _prepare_sanctions_and_adhoc_response(
    request: AuthenticatedHttpRequest,
    application: SanctionsAndAdhocApplication,
    context: dict[str, Any],
) -> HttpResponse:

    goods = annotate_commodity_unit(
        application.sanctionsandadhocapplicationgoods_set.all(), "commodity__"
    ).distinct()

    context.update({"process": application, "goods": goods})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-sanctions-response.html",
        context=context,
    )


def _prepare_derogations_response(
    request: AuthenticatedHttpRequest, application: DerogationsApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-derogations-response.html",
        context=context,
    )


def _prepare_wood_quota_response(
    request: AuthenticatedHttpRequest, application: WoodQuotaApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-wood-quota-response.html",
        context=context,
    )


def _prepare_opt_response(
    request: AuthenticatedHttpRequest,
    application: OutwardProcessingTradeApplication,
    context: dict[str, Any],
) -> HttpResponse:
    compensating_product_commodities = application.cp_commodities.all()
    temporary_exported_goods_commodities = application.teg_commodities.all()

    context.update(
        {
            "process": application,
            "compensating_product_commodities": compensating_product_commodities,
            "temporary_exported_goods_commodities": temporary_exported_goods_commodities,
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-opt-response.html",
        context=context,
    )


def _prepare_textiles_quota_response(
    request: AuthenticatedHttpRequest, application: TextilesApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-textiles-quota-response.html",
        context=context,
    )


def _prepare_sps_response(
    request: AuthenticatedHttpRequest,
    application: PriorSurveillanceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-sps-response.html",
        context=context,
    )


def _prepare_ironsteel_response(
    request: AuthenticatedHttpRequest,
    application: PriorSurveillanceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "certificates": application.certificates.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-ironsteel-response.html",
        context=context,
    )


def _prepare_com_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfManufactureApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-com-response.html",
        context=context,
    )


def _prepare_cfs_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfFreeSaleApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-cfs-response.html",
        context=context,
    )


def _prepare_gmp_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfGoodManufacturingPracticeApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-gmp-response.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def start_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        application_errors: ApplicationErrors = get_app_errors(model_class, application, case_type)

        if request.POST and not application_errors.has_errors():
            application.status = model_class.Statuses.PROCESSING
            application.save()

            task.is_active = False
            task.finished = timezone.now()
            task.save()

            Task.objects.create(
                process=application, task_type=Task.TaskType.AUTHORISE, previous=task
            )

            return redirect(reverse("workbasket"))

        else:
            context = {
                "case_type": case_type,
                "process": application,
                "task": task,
                "page_title": get_page_title(case_type, application, "Authorisation"),
                "errors": application_errors if application_errors.has_errors() else None,
            }

            return render(
                request=request,
                template_name="web/domains/case/authorisation.html",
                context=context,
            )


@login_required
@sensitive_post_parameters("password")
@permission_required("web.reference_data_access", raise_exception=True)
def authorise_documents(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.AUTHORISE)

        if request.POST:
            form = forms.AuthoriseForm(data=request.POST, request=request)

            if form.is_valid():
                # TODO: ICMSLST-809 Check validation that is needed when generating license file
                application.status = model_class.Statuses.COMPLETED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.owner = request.user
                task.save()

                messages.success(
                    request,
                    f"Authorise Success: Application {application.reference} has been authorised",
                )
                return redirect(reverse("workbasket"))
        else:
            form = forms.AuthoriseForm(request=request)

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "process": application,
            "task": task,
            "page_title": get_page_title(case_type, application, "Authorisation"),
            "form": form,
            "contacts": forms.application_contacts(application),
        }

        return render(
            request=request,
            template_name="web/domains/case/authorise-documents.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def view_document_packs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = _get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, "authorise")
        application_type = application.application_type

        if case_type == "import":
            cover_letter_flag = application_type.cover_letter_flag
            type_label = application_type.Types(application_type.type).label
            customs_copy = application_type.type == application_type.Types.OPT
            is_cfs = False
        else:
            cover_letter_flag = False
            type_label = application_type.type
            customs_copy = False
            is_cfs = application_type.type_code == application_type.Types.FREE_SALE

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "case_type": case_type,
            "process": application,
            "task": task,
            "cover_letter_flag": cover_letter_flag,
            "page_title": get_page_title(case_type, application, "Authorisation"),
            "contacts": forms.application_contacts(application),
            "type_label": type_label,
            "customs_copy": customs_copy,
            "is_cfs": is_cfs,
        }

        return render(
            request=request,
            template_name="web/domains/case/document-packs.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def cancel_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.AUTHORISE)

        application.status = model_class.Statuses.SUBMITTED
        application.save()

        task.is_active = False
        task.finished = timezone.now()
        task.owner = request.user
        task.save()

        Task.objects.create(process=application, task_type=Task.TaskType.PROCESS, previous=task)

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_case_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

    if application.process_type in [
        OpenIndividualLicenceApplication.PROCESS_TYPE,
        DFLApplication.PROCESS_TYPE,
        SILApplication.PROCESS_TYPE,
    ]:

        info_email = (
            "This screen is used to email relevant constabularies. You may attach multiple"
            " firearms certificates to a single email. You can also record responses from the constabulary."
        )
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        info_email = "Biocidal products: this screen is used to email and record responses from the Health and Safety Executive."

    else:
        info_email = ""

    context = {
        "process": application,
        "task": task,
        "page_title": "Manage Emails",
        "case_emails": application.case_emails.filter(is_active=True),
        "case_type": case_type,
        "info_email": info_email,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/case-emails.html",
        context=context,
    )


def _get_case_email_application(application: ImpOrExp) -> ApplicationsWithCaseEmail:
    # import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return application.openindividuallicenceapplication

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return application.dflapplication

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return application.silapplication

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return application.sanctionsandadhocapplication

    # certificate application
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return application.certificateoffreesaleapplication

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return application.certificateofgoodmanufacturingpracticeapplication

    else:
        raise Exception(f"CaseEmail for application not supported {application.process_type}")


def _create_email(application: ApplicationsWithCaseEmail) -> models.CaseEmail:
    # import applications
    if application.process_type in [
        OpenIndividualLicenceApplication.PROCESS_TYPE,
        DFLApplication.PROCESS_TYPE,
        SILApplication.PROCESS_TYPE,
    ]:
        template = Template.objects.get(is_active=True, template_code="IMA_CONSTAB_EMAIL")
        goods_description = (
            "Firearms, component parts thereof, or ammunition of any applicable"
            " commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended."
        )
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "IMPORTER_NAME": application.importer.display_name,
                "IMPORTER_ADDRESS": application.importer_office,
                "GOODS_DESCRIPTION": goods_description,
                "CASE_OFFICER_NAME": application.case_owner.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        cc_address_list = [settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        template = Template.objects.get(is_active=True, template_code="IMA_SANCTION_EMAIL")
        goods_descriptions = application.sanctionsandadhocapplicationgoods_set.values_list(
            "goods_description", flat=True
        )
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "IMPORTER_NAME": application.importer.display_name,
                "IMPORTER_ADDRESS": application.importer_office,
                "GOODS_DESCRIPTION": "\n".join(goods_descriptions),
                "CASE_OFFICER_NAME": application.case_owner.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        cc_address_list = []

    # certificate applications
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        template = Template.objects.get(is_active=True, template_code="CA_HSE_EMAIL")
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "APPLICATION_TYPE": ExportApplicationType.ProcessTypes.CFS.label,  # type: ignore[attr-defined]
                "EXPORTER_NAME": application.exporter,
                "EXPORTER_ADDRESS": application.exporter_office,
                "CONTACT_EMAIL": application.contact.email,
                "CERT_COUNTRIES": "\n".join(
                    application.countries.filter(is_active=True).values_list("name", flat=True)
                ),
                "SELECTED_PRODUCTS": _get_selected_product_data(
                    application.schedules.filter(legislations__is_biocidal=True)
                ),
                "CASE_OFFICER_NAME": application.case_owner.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        cc_address_list = []

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        template = Template.objects.get(is_active=True, template_code="CA_BEIS_EMAIL")
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "APPLICATION_TYPE": ExportApplicationType.ProcessTypes.GMP.label,  # type: ignore[attr-defined]
                "EXPORTER_NAME": application.exporter,
                "EXPORTER_ADDRESS": application.exporter_office,
                "MANUFACTURER_NAME": application.manufacturer_name,
                "MANUFACTURER_ADDRESS": application.manufacturer_address,
                "MANUFACTURER_POSTCODE": application.manufacturer_postcode,
                "RESPONSIBLE_PERSON_NAME": application.responsible_person_name,
                "RESPONSIBLE_PERSON_ADDRESS": application.responsible_person_address,
                "RESPONSIBLE_PERSON_POSTCODE": application.responsible_person_postcode,
                "BRAND_NAMES": ", ".join([b.brand_name for b in application.brands.all()]),
                "CASE_OFFICER_NAME": application.case_owner.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        cc_address_list = []

    else:
        raise Exception(f"CaseEmail for application not supported {application.process_type}")

    return models.CaseEmail.objects.create(
        status=models.CaseEmail.Status.DRAFT,
        subject=template.template_title,
        body=content,
        cc_address_list=cc_address_list,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def create_case_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        imp_exp_application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        application: ApplicationsWithCaseEmail = _get_case_email_application(imp_exp_application)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        email: models.CaseEmail = _create_email(application)
        application.case_emails.add(email)

        return redirect(
            reverse(
                "case:edit-case-email",
                kwargs={
                    "application_pk": application.pk,
                    "case_email_pk": email.pk,
                    "case_type": case_type,
                },
            )
        )


def _get_case_email_config(application: ApplicationsWithCaseEmail) -> CaseEmailConfig:
    # import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = File.objects.filter(
            Q(firearmsauthority__oil_application=application)
            | Q(userimportcertificate__oil_application=application)
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = application.goods_certificates.filter(is_active=True)

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == SILApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = File.objects.filter(
            Q(firearmsauthority__sil_application=application)
            | Q(userimportcertificate__sil_application=application)
            | Q(silusersection5__sil_application=application)
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in SanctionEmail.objects.filter(is_active=True)
        ]
        files = application.supporting_documents.filter(is_active=True)

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    # certificate application
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        choices = [(settings.ICMS_CFS_HSE_EMAIL, settings.ICMS_CFS_HSE_EMAIL)]
        files = File.objects.none()

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        choices = [(settings.ICMS_GMP_BEIS_EMAIL, settings.ICMS_GMP_BEIS_EMAIL)]

        app_files: "QuerySet[GMPFile]" = application.supporting_documents.filter(is_active=True)
        ft = GMPFile.Type
        ct = CertificateOfGoodManufacturingPracticeApplication.CertificateTypes

        if application.gmp_certificate_issued == ct.ISO_22716:
            files = app_files.filter(file_type__in=[ft.ISO_22716, ft.ISO_17021, ft.ISO_17065])
        elif application.gmp_certificate_issued == ct.BRC_GSOCP:
            files = app_files.filter(file_type=ft.BRC_GSOCP)
        else:
            files = File.objects.none()

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    else:
        raise Exception(f"CaseEmail for application not supported {application.process_type}")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        imp_exp_application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        application: ApplicationsWithCaseEmail = _get_case_email_application(imp_exp_application)

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email = get_object_or_404(
            application.case_emails.filter(is_active=True), pk=case_email_pk
        )

        case_email_config = _get_case_email_config(application)
        if request.POST:
            form = forms.CaseEmailForm(
                request.POST, instance=case_email, case_email_config=case_email_config
            )
            if form.is_valid():
                case_email = form.save()

                if "send" in request.POST:
                    attachments = []
                    s3_client = get_s3_client()

                    for document in case_email.attachments.all():
                        file_content = get_file_from_s3(document.path, client=s3_client)
                        attachments.append((document.filename, file_content))

                    email.send_email(
                        case_email.subject,
                        case_email.body,
                        [case_email.to],
                        case_email.cc_address_list,
                        attachments,
                    )

                    case_email.status = models.CaseEmail.Status.OPEN
                    case_email.sent_datetime = timezone.now()
                    case_email.save()

                    return redirect(
                        reverse(
                            "case:manage-case-emails",
                            kwargs={"application_pk": application_pk, "case_type": case_type},
                        )
                    )

                return redirect(
                    reverse(
                        "case:edit-case-email",
                        kwargs={
                            "application_pk": application_pk,
                            "case_email_pk": case_email_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            form = forms.CaseEmailForm(instance=case_email, case_email_config=case_email_config)

        context = {
            "process": application,
            "task": task,
            "page_title": "Edit Email",
            "form": form,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/edit-case-email.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        case_email = get_object_or_404(
            application.case_emails.filter(is_active=True), pk=case_email_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email.is_active = False
        case_email.save()

        return redirect(
            reverse(
                "case:manage-case-emails",
                kwargs={"application_pk": application_pk, "case_type": case_type},
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_response_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email = get_object_or_404(application.case_emails, pk=case_email_pk)

        if request.POST:
            form = forms.CaseEmailResponseForm(request.POST, instance=case_email)
            if form.is_valid():
                case_email = form.save(commit=False)
                case_email.status = models.CaseEmail.Status.CLOSED
                case_email.closed_datetime = timezone.now()
                case_email.save()

                return redirect(
                    reverse(
                        "case:manage-case-emails",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = forms.CaseEmailResponseForm(instance=case_email)

        context = {
            "process": application,
            "task": task,
            "page_title": "Add Response for Email",
            "form": form,
            "object": case_email,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/add-response-case-email.html",
            context=context,
        )


def get_page_title(case_type: str, application: ImpOrExpOrAccess, page: str) -> str:
    if case_type == "import":
        return f"{ImportApplicationType.ProcessTypes(application.process_type).label} - {page}"
    elif case_type == "export":
        return f"{ExportApplicationType.ProcessTypes(application.process_type).label} - {page}"
    elif case_type == "access":
        return "Access Request - {page}"
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def _get_selected_product_data(biocidal_schedules: "QuerySet[CFSSchedule]") -> str:
    products = CFSProduct.objects.filter(schedule__in=biocidal_schedules)
    product_data = []

    for p in products:
        p_types = (str(pk) for pk in p.product_type_numbers.values_list("pk", flat=True))
        ingredient_list = p.active_ingredients.values_list("name", "cas_number")
        ingredients = (f"{name} ({cas})" for name, cas in ingredient_list)

        product = "\n".join(
            [
                f"Product: {p.product_name}",
                f"Product type numbers: {', '.join(p_types)}",
                f"Active ingredients (CAS numbers): f{', '.join(ingredients)}",
            ]
        )
        product_data.append(product)

    return "\n\n".join(product_data)
