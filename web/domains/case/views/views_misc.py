from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from guardian.shortcuts import get_users_with_perms

from web.domains.template.models import Template
from web.domains.user.models import User
from web.flow.models import Task
from web.models import WithdrawApplication
from web.notify.email import send_email
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors

from .. import forms
from ..app_checks import get_app_errors
from ..types import ImpOrExp, ImpTypeOrExpType
from ..utils import (
    check_application_permission,
    get_application_current_task,
    get_case_page_title,
)
from .utils import get_class_imp_or_exp, get_current_task_and_readonly_status

if TYPE_CHECKING:
    from django.db.models import QuerySet


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

        messages.success(request, "Application has been canceled.")

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

        if application.current_update_requests():
            # application revert to prepare when update is requested
            task = get_application_current_task(application, case_type, Task.TaskType.PREPARE)
        else:
            task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.POST:
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

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        context = {
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "process": application,
            "task": task,
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

        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)

        if application.current_update_requests():
            # application revert to prepare when update is requested
            get_application_current_task(application, case_type, Task.TaskType.PREPARE)
        else:
            get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        withdrawal.is_active = False
        withdrawal.save()

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

        withdrawals = application.withdrawals.filter(is_active=True)
        current_withdrawal = withdrawals.filter(status=WithdrawApplication.STATUS_OPEN).first()

        if request.POST and not readonly_view:
            form = forms.WithdrawResponseForm(request.POST, instance=current_withdrawal)

            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.response_by = request.user
                withdrawal.save()

                # withdrawal accepted - case is closed, else case still open
                if withdrawal.status == WithdrawApplication.STATUS_ACCEPTED:
                    application.status = model_class.Status.WITHDRAWN
                    application.is_active = False
                    application.save()

                    task.is_active = False
                    task.owner = request.user
                    task.finished = timezone.now()
                    task.save()

                    return redirect(reverse("workbasket"))
                else:
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

        application.get_task(model_class.Statuses.SUBMITTED, Task.TaskType.PROCESS)

        application.case_owner = request.user
        application.status = model_class.Statuses.PROCESSING

        if case_type == "import":
            # Licence start date is set when ILB Admin takes the case
            application.licence_start_date = timezone.now().date()

        # TODO: Revisit when implementing ICMSLST-1169
        # We may need to create some more datetime fields

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

        application.status = model_class.Statuses.SUBMITTED
        application.case_owner = None
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

        if request.POST and not readonly_view:
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
            if application.decision == application.REFUSE:
                application.status = model_class.Statuses.COMPLETED
                next_task = Task.TaskType.REJECTED
            else:
                application.status = model_class.Statuses.PROCESSING
                next_task = Task.TaskType.AUTHORISE

            application.save()

            task.is_active = False
            task.finished = timezone.now()
            task.save()

            Task.objects.create(process=application, task_type=next_task, previous=task)

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

        if request.POST:
            form = forms.AuthoriseForm(data=request.POST, request=request)

            if form.is_valid():
                # TODO: ICMSLST-809 Check validation that is needed when generating license file
                task.is_active = False
                task.finished = timezone.now()
                task.owner = request.user
                task.save()

                # TODO: ICMSLST-812 chief document submission - update application.chief_usage_status
                if case_type == "import" and application.application_type.chief_flag:
                    Task.objects.create(
                        process=application, task_type=Task.TaskType.CHIEF_WAIT, previous=task
                    )
                else:
                    application.status = model_class.Statuses.COMPLETED
                    application.save()

                    Task.objects.create(
                        process=application, task_type=Task.TaskType.ACK, previous=task
                    )

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


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_document_packs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
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
            **get_document_context(case_type, application.application_type),
        }

        return render(
            request=request,
            template_name="web/domains/case/document-packs.html",
            context=context,
        )


def get_document_context(case_type: str, at: ImpTypeOrExpType) -> dict[str, str]:
    if case_type == "import":
        context = {
            "cover_letter_flag": at.cover_letter_flag,
            "type_label": at.Types(at.type).label,
            "customs_copy": at.type == at.Types.OPT,
            "is_cfs": False,
        }
    else:
        context = {
            "cover_letter_flag": False,
            "type_label": at.type,
            "customs_copy": False,
            "is_cfs": at.type_code == at.Types.FREE_SALE,
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

        # TODO ICMSLST-1220 change: Should be set to PROCESSING not SUBMITTED?
        # NOTE: This puts the application in a state that nobody can authorise - it should get the `Manage` action.
        application.status = model_class.Statuses.SUBMITTED
        application.save()

        task.is_active = False
        task.finished = timezone.now()
        task.owner = request.user
        task.save()

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

        task = get_application_current_task(application, case_type, Task.TaskType.ACK)

        if request.POST:
            form = forms.AckReceiptForm(request.POST)
            if form.is_valid():
                application.acknowledged_by = request.user
                application.acknowledged_datetime = timezone.now()
                application.save()

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
            "task": task,
            "process_template": f"web/domains/case/{case_type}/partials/process.html",
            "form": form,
            "primary_recipients": _get_primary_recipients(application),
            "copy_recipients": _get_copy_recipients(application),
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Response"),
            "acknowledged": application.acknowledged_by and application.acknowledged_datetime,
            "org": org,
            "show_generation_status": False,
            **get_document_context(case_type, application.application_type),
        }

        return render(
            request=request,
            template_name="web/domains/case/ack-notification.html",
            context=context,
        )


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
