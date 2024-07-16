from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case import forms
from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import end_process_task, get_case_page_title
from web.domains.template.utils import get_application_update_template_data
from web.mail.emails import (
    send_application_update_email,
    send_application_update_withdrawn_email,
)
from web.models import Task, UpdateRequest, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest

from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp


#
# *****************************************************************************
# The following views are ILB Admin only views
# *****************************************************************************
#
def check_ilb_permission(application: ImpOrExp, case_type: str, user: User) -> None:
    """Raise PermissionDenied unless the view is editable by the supplied user.

    This checks user is the assigned caseworker and the application has the correct status
    and associated tasks.
    """

    readonly_view = get_caseworker_view_readonly_status(application, case_type, user)

    if readonly_view:
        raise PermissionDenied


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_GET
def list_update_requests(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """ILB Admin view listing all update requests for a given application."""

    model_class = get_class_imp_or_exp(case_type)

    application: ImpOrExp = get_object_or_404(model_class, pk=application_pk)

    readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

    update_requests = application.update_requests.filter(is_active=True)
    update_request = update_requests.filter(
        status__in=[
            UpdateRequest.Status.DRAFT,
            UpdateRequest.Status.OPEN,
            UpdateRequest.Status.UPDATE_IN_PROGRESS,
            UpdateRequest.Status.RESPONDED,
        ]
    ).first()
    previous_update_requests = update_requests.filter(status=UpdateRequest.Status.CLOSED)

    context = {
        "process": application,
        "page_title": get_case_page_title(case_type, application, "Update Requests"),
        "previous_update_requests": previous_update_requests.order_by("-pk"),
        "update_request": update_request,
        "has_any_update_requests": update_requests.exists(),
        "case_type": case_type,
        "readonly_view": readonly_view,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/update-requests/list.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def add_update_request(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """ILB Admin view to add a draft update request."""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_ilb_permission(application, case_type, request.user)

        email_subject, email_content = get_application_update_template_data(application)

        ur = application.update_requests.create(
            status=UpdateRequest.Status.DRAFT,
            request_subject=email_subject,
            request_detail=email_content,
        )

        return redirect(
            reverse(
                "case:edit-update-request",
                kwargs={
                    "application_pk": application_pk,
                    "update_request_pk": ur.pk,
                    "case_type": case_type,
                },
            )
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_update_request(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    update_request_pk: int,
    case_type: str,
) -> HttpResponse:
    """ILB Admin view to edit / send an update request to an applicant."""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_ilb_permission(application, case_type, request.user)

        try:
            update_request = get_object_or_404(
                application.update_requests, pk=update_request_pk, status=UpdateRequest.Status.DRAFT
            )
        except ObjectDoesNotExist:
            messages.warning(request, "Update Request is no longer available")
            return redirect(
                reverse(
                    "case:list-update-requests",
                    kwargs={"application_pk": application_pk, "case_type": case_type},
                )
            )

        if request.method == "POST":
            task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

            form = forms.UpdateRequestForm(request.POST, instance=update_request)
            if form.is_valid():
                update_request = form.save()

                if "send" in form.data:
                    update_request.requested_by = request.user
                    update_request.request_datetime = timezone.now()
                    update_request.status = UpdateRequest.Status.OPEN
                    update_request.save()

                    Task.objects.create(
                        process=application, task_type=Task.TaskType.PREPARE, previous=task
                    )
                    send_application_update_email(update_request)
                    application.update_order_datetime()
                    application.save()

                return redirect(
                    reverse(
                        "case:list-update-requests",
                        kwargs={"application_pk": application.pk, "case_type": case_type},
                    )
                )

        else:
            form = forms.UpdateRequestForm(instance=update_request)

        previous_update_requests = application.update_requests.filter(
            is_active=True, status=UpdateRequest.Status.CLOSED
        )
        context = {
            "process": application,
            "page_title": get_case_page_title(case_type, application, "Update Requests"),
            "form": form,
            "previous_update_requests": previous_update_requests.order_by("-pk"),
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/update-requests/edit.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def delete_update_request(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    update_request_pk: int,
    case_type: str,
) -> HttpResponse:
    """ILB Admin view to delete a draft update request."""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_ilb_permission(application, case_type, request.user)

        try:
            update_request = get_object_or_404(
                application.update_requests, pk=update_request_pk, status=UpdateRequest.Status.DRAFT
            )
        except ObjectDoesNotExist:
            messages.warning(request, "Update Request is no longer available")
            return redirect(
                reverse(
                    "case:list-update-requests",
                    kwargs={"application_pk": application_pk, "case_type": case_type},
                )
            )

        update_request.is_active = False
        update_request.status = UpdateRequest.Status.DELETED
        update_request.response_detail = "Request was deleted by ILB and marked inactive."
        update_request.closed_by = request.user
        update_request.save()

    return redirect(
        reverse(
            "case:list-update-requests",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def close_update_request(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    update_request_pk: int,
    case_type: str,
) -> HttpResponse:
    """ILB Admin view to close or withdraw an update request."""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_ilb_permission(application, case_type, request.user)

        update_request = get_object_or_404(application.update_requests, pk=update_request_pk)

        if update_request.status not in [UpdateRequest.Status.OPEN, UpdateRequest.Status.RESPONDED]:
            messages.warning(
                request,
                "Unable to close Update Request. Status must be Open or Responded to close.",
            )

            return redirect(
                reverse(
                    "case:list-update-requests",
                    kwargs={"application_pk": application_pk, "case_type": case_type},
                )
            )

        # The update request has been withdrawn so revert to draft.
        if update_request.status == UpdateRequest.Status.OPEN:
            update_request.status = UpdateRequest.Status.DRAFT
            update_request.save()

            # Close the task created when sending the update request.
            task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)
            end_process_task(task, request.user)

            send_application_update_withdrawn_email(update_request)

        # Close the responded update request.
        else:
            update_request.status = UpdateRequest.Status.CLOSED
            update_request.closed_by = request.user
            update_request.closed_datetime = timezone.now()
            update_request.save()

    return redirect(
        reverse(
            "case:list-update-requests",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
    )


#
# *****************************************************************************
# The following views are applicant only views
# *****************************************************************************
#
def check_can_edit_application(user: User, application: ImpOrExp) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def start_update_request(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    update_request_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        case_progress.check_expected_status(
            application,
            [ImpExpStatus.SUBMITTED, ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED],
        )

        update_requests = application.update_requests.filter(is_active=True)
        try:
            update_request = update_requests.get(
                pk=update_request_pk, is_active=True, status=UpdateRequest.Status.OPEN
            )
        except ObjectDoesNotExist:
            messages.warning(
                request, "Update Request has been withdrawn and is no longer available"
            )
            return redirect(reverse("workbasket"))

        previous_update_requests = update_requests.filter(status=UpdateRequest.Status.CLOSED)

        if request.method == "POST":
            update_request.status = UpdateRequest.Status.UPDATE_IN_PROGRESS
            update_request.save()

            application.update_order_datetime()
            application.save()

            return redirect(
                reverse(
                    "case:respond-update-request",
                    kwargs={
                        "case_type": case_type,
                        "application_pk": application_pk,
                    },
                )
            )

        context = {
            "process": application,
            "case_type": case_type,
            "update_request": update_request,
            "previous_update_requests": previous_update_requests.order_by("-pk"),
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
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        update_requests = application.update_requests.filter(is_active=True)
        update_request = update_requests.get(
            status__in=[
                UpdateRequest.Status.UPDATE_IN_PROGRESS,
                UpdateRequest.Status.RESPONDED,
            ]
        )
        previous_update_requests = update_requests.filter(status=UpdateRequest.Status.CLOSED)

        if request.method == "POST":
            form = forms.UpdateRequestResponseForm(request.POST, instance=update_request)
            if form.is_valid():
                update_request = form.save(commit=False)

                update_request.response_by = request.user
                update_request.response_datetime = timezone.now()
                update_request.save()

                application.update_order_datetime()
                application.save()

                return redirect(
                    reverse(
                        application.get_edit_view_name(),
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            form = forms.UpdateRequestResponseForm(instance=update_request)

        context = {
            "process": application,
            "case_type": case_type,
            "form": form,
            "update_request": update_request,
            "previous_update_requests": previous_update_requests.order_by("-pk"),
        }

        return render(
            request=request,
            template_name="web/domains/case/respond-update-request.html",
            context=context,
        )
