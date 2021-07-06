from typing import TYPE_CHECKING, Any, NamedTuple, Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from guardian.shortcuts import get_users_with_perms

from web.domains.case._import.derogations.forms import DerogationsChecklistForm
from web.domains.case._import.fa_dfl.forms import DFLChecklistForm
from web.domains.case._import.fa_oil.forms import ChecklistFirearmsOILApplicationForm
from web.domains.case._import.fa_sil.forms import SILChecklistForm
from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.opt.forms import (
    FurtherQuestionsBaseOPTForm,
    OPTChecklistForm,
)
from web.domains.case._import.opt.utils import get_fq_form, get_fq_page_name
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case._import.wood.forms import WoodQuotaChecklistForm
from web.domains.file.utils import create_file_model
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
    ExporterAccessRequest,
    ImportApplication,
    ImporterAccessRequest,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    OutwardProcessingTradeFile,
    SanctionsAndAdhocApplication,
    SILApplication,
    WithdrawApplication,
    WoodQuotaApplication,
)
from web.notify import notify
from web.notify.email import send_email
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from . import forms, models
from .fir import forms as fir_forms
from .fir.models import FurtherInformationRequest

if TYPE_CHECKING:
    from django.db.models import QuerySet


ImpOrExp = Union[ImportApplication, ExportApplication]
ImpOrExpT = Type[ImpOrExp]

ImpOrExpOrAccess = Union[ImportApplication, ExportApplication, AccessRequest]
ImpOrExpOrAccessT = Type[ImpOrExpOrAccess]


ApplicationsWithChecklist = Union[
    OpenIndividualLicenceApplication,
    DFLApplication,
    SILApplication,
    WoodQuotaApplication,
    DerogationsApplication,
    OutwardProcessingTradeApplication,
]


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

        is_contact = application.user_is_contact_of_org(user)

        if not _has_importer_exporter_access(user, case_type) or not is_contact:
            raise PermissionDenied

    else:
        # Should never get here.
        raise PermissionDenied


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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        context = {
            "process": application,
            "notes": application.case_notes,
            "case_type": case_type,
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        note = application.case_notes.get(pk=note_pk)

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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
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
    has_access = _has_importer_exporter_access(request.user, case_type)
    if not has_access:
        raise PermissionDenied

    with transaction.atomic():
        model_class = _get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )

        if not application.user_is_contact_of_org(request.user):
            raise PermissionDenied

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

                Task.objects.create(process=application, task_type="process", previous=task)

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Management",
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
    has_access = _has_importer_exporter_access(request.user, case_type)
    if not has_access:
        raise PermissionDenied

    with transaction.atomic():
        model_class = _get_class_imp_or_exp(case_type)
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)

        task = application.get_task(model_class.Statuses.WITHDRAWN, "process")

        if not application.user_is_contact_of_org(request.user):
            raise PermissionDenied

        application.status = model_class.Statuses.SUBMITTED
        application.save()

        withdrawal.is_active = False
        withdrawal.save()

        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=application, task_type="process", previous=task)

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_update_requests(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )

        update_requests = application.update_requests.filter(is_active=True)
        current_update_request = update_requests.filter(
            status__in=[models.UpdateRequest.OPEN, models.UpdateRequest.UPDATE_IN_PROGRESS]
        ).first()

        if case_type == "import":
            template_code = "IMA_APP_UPDATE"

            # TODO: replace with case reference ICMSLST-348
            placeholder_content = {
                "CASE_REFERENCE": application_pk,
                "IMPORTER_NAME": application.importer.display_name,
                "CASE_OFFICER_NAME": request.user,
            }
        elif case_type == "export":
            template_code = "CA_APPLICATION_UPDATE_EMAIL"

            # TODO: replace with case reference ICMSLST-348
            placeholder_content = {
                "CASE_REFERENCE": application_pk,
                "EXPORTER_NAME": application.exporter.name,
                "CASE_OFFICER_NAME": request.user,
            }

        # TODO: replace with case reference ICMSLST-348
        template = Template.objects.get(template_code=template_code, is_active=True)
        email_subject = template.get_title({"CASE_REFERENCE": application_pk})
        email_content = template.get_content(placeholder_content)

        if request.POST:
            form = forms.UpdateRequestForm(request.POST)
            if form.is_valid():
                update_request = form.save(commit=False)
                update_request.requested_by = request.user
                update_request.request_datetime = timezone.now()
                update_request.status = models.UpdateRequest.OPEN
                update_request.save()

                application.status = model_class.Statuses.UPDATE_REQUESTED
                application.save()
                application.update_requests.add(update_request)

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="prepare", previous=task)

                if case_type == "import":
                    contacts = get_users_with_perms(
                        application.importer, only_with_perms_in=["is_contact_of_importer"]
                    ).filter(user_permissions__codename="importer_access")
                elif case_type == "export":
                    contacts = get_users_with_perms(
                        application.exporter, only_with_perms_in=["is_contact_of_exporter"]
                    ).filter(user_permissions__codename="exporter_access")

                notify.update_request(
                    update_request.request_subject,
                    update_request.request_detail,
                    contacts,
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

        context = {
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Update Requests",
            "form": form,
            "update_requests": update_requests,
            "current_update_request": current_update_request,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/update-requests.html",
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        update_request = get_object_or_404(application.update_requests, pk=update_request_pk)

        update_request.status = models.UpdateRequest.CLOSED
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
@permission_required("web.reference_data_access", raise_exception=True)
def manage_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(model_class.Statuses.SUBMITTED, "process")

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
            "page_title": "Further Information Requests",
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
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        template = Template.objects.get(template_code="IAR_RFI_EMAIL", is_active=True)
        # TODO: use case reference
        title_mapping = {"REQUEST_REFERENCE": application.pk}
        content_mapping = {
            "REQUESTER_NAME": application.submitted_by,
            "CURRENT_USER_NAME": request.user,
            "REQUEST_REFERENCE": application.pk,
        }
        fir = application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=template.get_title(title_mapping),
            request_detail=template.get_content(content_mapping),
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        Task.objects.create(process=fir, task_type="check_draft", owner=request.user)

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

        task = application.get_task(model_class.Statuses.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.DRAFT, "check_draft")

        if request.POST:
            form = fir_forms.FurtherInformationRequestForm(request.POST, instance=fir)

            if form.is_valid():
                fir = form.save()

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()
                    notify.further_information_requested(fir, contacts)

                    fir_task.is_active = False
                    fir_task.finished = timezone.now()
                    fir_task.save()

                    Task.objects.create(process=fir, task_type="notify_contacts", previous=fir_task)

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

        application.get_task(model_class.Statuses.SUBMITTED, "process")
        fir_tasks = fir.get_active_tasks()

        fir.is_active = False
        fir.status = FurtherInformationRequest.DELETED
        fir.save()

        fir_tasks.update(is_active=False, finished=timezone.now())

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

        application.get_task(model_class.Statuses.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        Task.objects.create(process=fir, task_type="check_draft", previous=fir_task)

        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=True, status=FurtherInformationRequest.DRAFT
        )

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
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        fir_task = fir.get_task(
            [FurtherInformationRequest.OPEN, FurtherInformationRequest.RESPONDED], "responded"
        )

        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=False, status=FurtherInformationRequest.CLOSED
        )

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
        application.get_task(model_class.Statuses.SUBMITTED, "process")

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
        application.get_task(model_class.Statuses.SUBMITTED, "process")

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
        application.get_task(model_class.Statuses.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        if request.POST:
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir, data=request.POST)

            if form.is_valid():
                fir = form.save()

                fir.response_datetime = timezone.now()
                fir.status = FurtherInformationRequest.RESPONDED
                fir.response_by = request.user
                fir.save()

                fir_task.is_active = False
                fir_task.finished = timezone.now()
                fir_task.save()

                Task.objects.create(process=fir, task_type="responded", owner=request.user)

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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )
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

                    Task.objects.create(process=application, task_type="process", previous=task)

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
            "page_title": f"{application.application_type.get_type_description()} - Withdrawals",
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

    if case_type == "access":
        # TODO: existing code in access/views.py did not check for any
        # permissions...we probably should
        pass
    else:
        has_imp_or_exp_access = _has_importer_exporter_access(request.user, case_type)
        has_perm_reference_data = request.user.has_perm("web.reference_data_access")

        if not has_imp_or_exp_access and not has_perm_reference_data:
            raise PermissionDenied

        # first check is for case managers (who are not marked as contacts of
        # importers), second is for people submitting applications
        assert isinstance(application, (ImportApplication, ExportApplication))

        is_contact = application.user_is_contact_of_org(request.user)
        if not has_perm_reference_data and not is_contact:
            raise PermissionDenied

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

    elif application.process_type == ImporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.importeraccessrequest)  # type: ignore[union-attr]

    elif application.process_type == ExporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.exporteraccessrequest)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfManufactureApplication.PROCESS_TYPE:
        return _view_com(request, application.certificateofmanufactureapplication)  # type: ignore[union-attr]

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return _view_dfl(request, application.dflapplication)  # type: ignore[union-attr]

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        return _view_opt(request, application.outwardprocessingtradeapplication)  # type: ignore[union-attr]

    elif application.process_type == TextilesApplication.PROCESS_TYPE:
        return _view_textiles_quota(request, application.textilesapplication)  # type: ignore[union-attr]
    else:
        raise NotImplementedError(f"Unknown process_type {application.process_type}")


def _view_fa_oil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/view_firearms_oil_case.html", context)


def _view_fa_sil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "verified_section5": application.importer.section5_authorities.currently_active(),
        "user_section5": application.user_section5.filter(is_active=True),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/view_firearms_sil_case.html", context)


def _view_sanctions_and_adhoc(
    request: AuthenticatedHttpRequest, application: SanctionsAndAdhocApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "goods": application.sanctionsandadhocapplicationgoods_set.all(),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/view_sanctions_and_adhoc_case.html", context)


def _view_wood_quota(
    request: AuthenticatedHttpRequest, application: WoodQuotaApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
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
        "page_title": application.application_type.get_type_description(),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/view_derogations.html", context)


def _view_dfl(request: AuthenticatedHttpRequest, application: DFLApplication) -> HttpResponse:
    goods_list = application.goods_certificates.filter(is_active=True).select_related(
        "issuing_country"
    )
    contact_list = application.importcontact_set.all()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
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
        "page_title": application.application_type.get_type_description(),
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
        "page_title": application.application_type.get_type_description(),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/textiles/view.html", context)


def _view_accessrequest(
    request: AuthenticatedHttpRequest, application: AccessRequest
) -> HttpResponse:
    context = {"process": application}

    return render(request, "web/domains/case/access/case-view.html", context)


def _view_com(
    request: AuthenticatedHttpRequest, application: CertificateOfManufactureApplication
) -> HttpResponse:
    # TODO: implement (ICMSLST-678)
    raise NotImplementedError


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def take_ownership(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )
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
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )

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
            "page_title": f"{application.application_type.get_type_description()} - Manage",
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

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.ResponsePreparationForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = forms.ResponsePreparationForm()

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
            "page_title": "Response Preparation",
            "form": form,
            "cover_letter_flag": cover_letter_flag,
            "electronic_licence_flag": electronic_licence_flag,
            # Not used currently but the template probably should.
            # Once the data is confirmed to be correct
            "endorsements_flag": endorsements_flag,
        }

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

    # TODO: implement other types (export-COM)
    else:
        raise NotImplementedError


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
    context.update(
        {"process": application, "goods": application.sanctionsandadhocapplicationgoods_set.all()}
    )

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


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def start_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [model_class.Statuses.SUBMITTED, model_class.Statuses.WITHDRAWN], "process"
        )

        application_errors = ApplicationErrors()

        prepare_errors = PageErrors(
            page_name="Response Preparation",
            url=reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": case_type},
            ),
        )

        if case_type == "import":
            _get_import_errors(application, application_errors, prepare_errors)

        elif case_type == "export":
            _get_export_errors(application, application_errors, prepare_errors)

        # Import & export checks
        if application.decision == model_class.REFUSE:
            prepare_errors.add(
                FieldError(field_name="Decision", messages=["Please approve application."])
            )

        application_errors.add(prepare_errors)

        if request.POST and not application_errors.has_errors():
            application.status = model_class.Statuses.PROCESSING
            application.save()

            return redirect(reverse("workbasket"))

        else:
            context = {
                "case_type": case_type,
                "process": application,
                "task": task,
                "page_title": "Authorisation",
                "errors": application_errors if application_errors.has_errors() else None,
            }

            return render(
                request=request,
                template_name="web/domains/case/authorisation.html",
                context=context,
            )


def _get_import_errors(application, application_errors, prepare_errors):
    # Application specific checks
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        application_errors.add(_get_fa_oil_errors(application))

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        application_errors.add(_get_fa_dfl_errors(application))

    elif application.process_type == SILApplication.PROCESS_TYPE:
        application_errors.add(_get_fa_sil_errors(application))

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        application_errors.add(_get_wood_errors(application))

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        application_errors.add(_get_derogations_errors(application))

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        application_errors.add(_get_opt_errors(application))

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        # There are no extra checks for Sanctions and Adhoc
        pass

    else:
        raise NotImplementedError(
            f"process_type {application.process_type!r} hasn't been implemented yet."
        )

    start_date = application.licence_start_date
    end_date = application.licence_end_date

    if not start_date:
        prepare_errors.add(
            FieldError(field_name="Licence start date", messages=["Licence start date missing."])
        )

    if not end_date:
        prepare_errors.add(
            FieldError(field_name="Licence end date", messages=["Licence end date missing."])
        )

    if start_date and end_date and end_date <= start_date:
        prepare_errors.add(
            FieldError(
                field_name="Licence end date", messages=["End date must be after the start date."]
            )
        )

    app_t: ImportApplicationType = application.application_type

    if app_t.paper_licence_flag and app_t.electronic_licence_flag:
        if application.issue_paper_licence_only is None:
            prepare_errors.add(
                FieldError(
                    field_name="Issue paper licence only?", messages=["You must enter this item"]
                )
            )

    if app_t.cover_letter_flag:
        if not application.cover_letter:
            prepare_errors.add(
                FieldError(field_name="Cover Letter", messages=["You must enter this item"])
            )


def _get_fa_oil_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.openindividuallicenceapplication,  # type: ignore[union-attr]
        "import:fa-oil:manage-checklist",
        ChecklistFirearmsOILApplicationForm,
    )


def _get_fa_dfl_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.dflapplication, "import:fa-dfl:manage-checklist", DFLChecklistForm  # type: ignore[union-attr]
    )


def _get_fa_sil_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.silapplication, "import:fa-sil:manage-checklist", SILChecklistForm  # type: ignore[union-attr]
    )


def _get_wood_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.woodquotaapplication, "import:wood:manage-checklist", WoodQuotaChecklistForm  # type: ignore[union-attr]
    )


def _get_derogations_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.derogationsapplication,  # type: ignore[union-attr]
        "import:derogations:manage-checklist",
        DerogationsChecklistForm,
    )


def _get_opt_errors(application: ImportApplication) -> PageErrors:
    return _get_checklist_errors(
        application.outwardprocessingtradeapplication,  # type: ignore[union-attr]
        "import:opt:manage-checklist",
        OPTChecklistForm,
    )


def _get_checklist_errors(
    application: ApplicationsWithChecklist,
    manage_checklist_url: str,
    checklist_form: Type[ChecklistBaseForm],
):

    checklist_errors = PageErrors(
        page_name="Checklist",
        url=reverse(manage_checklist_url, kwargs={"application_pk": application.pk}),
    )

    try:
        create_page_errors(
            checklist_form(
                data=model_to_dict(application.checklist), instance=application.checklist
            ),
            checklist_errors,
        )

    except ObjectDoesNotExist:
        checklist_errors.add(
            FieldError(field_name="Checklist", messages=["Please complete checklist."])
        )

    return checklist_errors


def _get_export_errors(application, application_errors, prepare_errors):
    raise NotImplementedError(
        f"process_type {application.process_type!r} hasn't been implemented yet."
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def cancel_authorisation(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = _get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(  # type: ignore[assignment]
            model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.Statuses.PROCESSING, "process")

        application.status = model_class.Statuses.SUBMITTED
        application.save()

        return redirect(reverse("workbasket"))
