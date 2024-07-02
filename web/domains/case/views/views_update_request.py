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
from web.mail.emails import send_application_update_email
from web.models import Task, UpdateRequest, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest

from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp


def check_can_edit_application(user: User, application: ImpOrExp) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_GET
def list_update_requests(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    application: ImpOrExp = get_object_or_404(model_class, pk=application_pk)

    readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

    update_requests = application.update_requests.filter(is_active=True)
    update_request = update_requests.filter(
        status__in=[
            UpdateRequest.Status.OPEN,
            UpdateRequest.Status.UPDATE_IN_PROGRESS,
            UpdateRequest.Status.RESPONDED,
        ]
    ).first()
    previous_update_requests = update_requests.filter(status=UpdateRequest.Status.CLOSED)

    context = {
        "process": application,
        "page_title": get_case_page_title(case_type, application, "Update Requests"),
        "previous_update_requests": previous_update_requests,
        "update_request": update_request,
        "has_any_update_requests": update_requests.exists(),
        "case_type": case_type,
        "readonly_view": readonly_view,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/list-update-requests.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_update_requests(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    """Allows admin to submit an update request to the applicant"""

    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)
        email_subject, email_content = get_application_update_template_data(application)

        if request.method == "POST" and not readonly_view:
            task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

            form = forms.UpdateRequestForm(request.POST)
            if form.is_valid():
                update_request = form.save(commit=False)
                update_request.requested_by = request.user
                update_request.request_datetime = timezone.now()
                update_request.status = UpdateRequest.Status.OPEN
                update_request.save()

                application.update_requests.add(update_request)

                Task.objects.create(
                    process=application, task_type=Task.TaskType.PREPARE, previous=task
                )
                send_application_update_email(update_request)
                application.update_order_datetime()
                application.save()

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
            status__in=[UpdateRequest.Status.OPEN, UpdateRequest.Status.RESPONDED]
        ).first()
        previous_update_requests = update_requests.filter(status=UpdateRequest.Status.CLOSED)

        context = {
            "process": application,
            "page_title": get_case_page_title(case_type, application, "Update Requests"),
            "form": form,
            "previous_update_requests": previous_update_requests,
            "update_request": update_request,
            "has_any_update_requests": update_requests.exists(),
            "case_type": case_type,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/update-requests.html",
            context=context,
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
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

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

        # The update request has been withdrawn therefore we can delete.
        if update_request.status == UpdateRequest.Status.OPEN:
            update_request.status = UpdateRequest.Status.DELETED
            update_request.response_detail = "Request was withdrawn by ILB and marked inactive."
            update_request.is_active = False
            update_request.closed_by = request.user
            update_request.save()

            # TODO: ICMSLST-2742 Send Withdraw Application Update email here
            #       Or at the end of the view (as it's a task).

        # Close the responded update request.
        else:
            update_request.status = UpdateRequest.Status.CLOSED
            update_request.closed_by = request.user
            update_request.closed_datetime = timezone.now()
            update_request.save()

        # If there are no more active update requests check for an optional process task.
        # There will be one if the ILB Admin closes the update request before the applicant
        # has responded (e.g. one was opened in error).
        if not (
            application.update_requests.filter(is_active=True)
            .exclude(status=UpdateRequest.Status.CLOSED)
            .exists()
        ):
            process_task = (
                case_progress.get_active_tasks(application, select_for_update=True)
                .filter(task_type=Task.TaskType.PREPARE)
                .first()
            )
            if process_task:
                end_process_task(process_task, request.user)

    return redirect(
        reverse(
            "case:list-update-requests",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
    )


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
            "previous_update_requests": previous_update_requests,
        }

        return render(
            request=request,
            template_name="web/domains/case/respond-update-request.html",
            context=context,
        )
