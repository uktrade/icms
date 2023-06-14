from typing import Literal

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.fir.forms import (
    FurtherInformationRequestForm,
    FurtherInformationRequestResponseForm,
)
from web.domains.case.forms import DocumentForm
from web.domains.case.services import case_progress
from web.domains.case.types import ImpOrExpOrAccess
from web.domains.case.utils import get_case_page_title
from web.domains.file.utils import create_file_model
from web.domains.template.utils import get_fir_template_data
from web.flow.models import ProcessTypes
from web.models import FurtherInformationRequest, User
from web.notify import notify
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3

from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp_or_access

CASE_TYPES = Literal["import", "export", "access"]


def _check_process_state(application: ImpOrExpOrAccess, case_type: CASE_TYPES):
    """Check a Process instance is being processed by a caseworker.

    Access requests and import/export applications check different statuses.
    """

    match case_type.casefold():
        case "access":
            case_progress.access_request_in_processing(application)
        case "import" | "export":
            case_progress.application_in_processing(application)
        case _:
            raise ValueError(f"Unknown Case type: {case_type}")


def _check_process_permission(
    user: User, application: ImpOrExpOrAccess, case_type: CASE_TYPES
) -> None:
    """Check a user has the correct access to modify / access a further information request."""

    match case_type.casefold():
        case "access":
            if user != application.submitted_by:
                raise PermissionDenied
        case "import" | "export":
            checker = AppChecker(user, application)

            if not checker.can_edit():
                raise PermissionDenied
        case _:
            raise ValueError(f"Unknown Case type: {case_type}")


#
# *****************************************************************************
# The following views are ILB Admin only views
# *****************************************************************************
#
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        # Access requests don't have a case_owner so can't call get_caseworker_view_readonly_status
        if application.process_type in [ProcessTypes.EAR, ProcessTypes.IAR]:
            _check_process_state(application, case_type)
            readonly_view = False
        else:
            readonly_view = get_caseworker_view_readonly_status(
                application, case_type, request.user
            )

        context = {
            "process": application,
            "firs": application.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ).filter(is_active=True),
            "case_type": case_type,
            "page_title": get_case_page_title(
                case_type, application, "Further Information Requests"
            ),
            "readonly_view": readonly_view,
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def add_fir(request, *, application_pk: int, case_type: CASE_TYPES) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        _check_process_state(application, case_type)
        subject, body = get_fir_template_data(application, request.user)

        fir = application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=subject,
            request_detail=body,
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

    return redirect(
        reverse(
            "case:edit-fir",
            kwargs={"application_pk": application_pk, "fir_pk": fir.pk, "case_type": case_type},
        )
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_fir(request, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        _check_process_state(application, case_type)

        fir = get_object_or_404(application.further_information_requests.draft(), pk=fir_pk)

        if request.method == "POST":
            form = FurtherInformationRequestForm(request.POST, instance=fir)

            if form.is_valid():
                fir = form.save()

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()

                    notify.send_further_information_request(application, fir)

                    application.update_order_datetime()
                    application.save()

                return _manage_fir_redirect(application_pk, case_type)
        else:
            form = FurtherInformationRequestForm(instance=fir)

        context = {
            "process": application,
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def delete_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        _check_process_state(application, case_type)

        fir.is_active = False
        fir.status = FurtherInformationRequest.DELETED
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def withdraw_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        _check_process_state(application, case_type)

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

        notify.send_further_information_request_withdrawal(application, fir)

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def close_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        _check_process_state(application, case_type)

        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def add_fir_file(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    redirect_url = "case:edit-fir"
    template_name = "web/domains/case/fir/add-fir-file.html"

    return _add_fir_file(
        request,
        application_pk,
        fir_pk,
        case_type,
        redirect_url,
        template_name,
        # Perms.sys.ilb_admin already checked so don't check more permissions.
        check_permission=False,
    )


#
# *****************************************************************************
# The following views are shared between an ILB Admin and an applicant
# *****************************************************************************
#
@login_required
def add_fir_response_file(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    redirect_url = "case:respond-fir"
    template_name = "web/domains/case/fir/add-fir-response-file.html"

    return _add_fir_file(request, application_pk, fir_pk, case_type, redirect_url, template_name)


def _add_fir_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    case_type: CASE_TYPES,
    redirect_url: str,
    template_name: str,
    *,
    check_permission: bool = True,
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)

        if check_permission:
            _check_process_permission(request.user, application, case_type)

        fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

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
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "fir": fir,
            "case_type": case_type,
            "prev_link": redirect_url,
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
    case_type: CASE_TYPES,
) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)
    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)

    if not request.user.has_perm(Perms.sys.ilb_admin):
        _check_process_permission(request.user, application, case_type)

    fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

    document = fir.files.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def delete_fir_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: CASE_TYPES,
) -> HttpResponse:
    redirect_url = "case:edit-fir"

    return _delete_fir_file(
        request.user,
        application_pk,
        fir_pk,
        file_pk,
        case_type,
        redirect_url,
        # Perms.sys.ilb_admin already checked so don't check more permissions.
        check_permission=False,
    )


@login_required
@require_POST
def delete_fir_response_file(
    request: AuthenticatedHttpRequest,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: CASE_TYPES,
):
    redirect_url = "case:respond-fir"

    return _delete_fir_file(request.user, application_pk, fir_pk, file_pk, case_type, redirect_url)


def _delete_fir_file(
    user: User,
    application_pk: int,
    fir_pk: int,
    file_pk: int,
    case_type: CASE_TYPES,
    redirect_url: str,
    *,
    check_permission: bool = True,
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        if check_permission:
            _check_process_permission(user, application, case_type)

        document = application.further_information_requests.get(pk=fir_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            redirect_url,
            kwargs={"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type},
        )
    )


#
# *****************************************************************************
# The following views are applicant only views
# *****************************************************************************
#
@login_required
def list_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)

    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)

    _check_process_permission(request.user, application, case_type)
    _check_process_state(application, case_type)

    context = {
        "process": application,
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
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: CASE_TYPES
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        _check_process_permission(request.user, application, case_type)
        _check_process_state(application, case_type)

        fir = get_object_or_404(application.further_information_requests.open(), pk=fir_pk)

        if request.method == "POST":
            form = FurtherInformationRequestResponseForm(instance=fir, data=request.POST)

            if form.is_valid():
                fir = form.save(commit=False)
                fir.response_datetime = timezone.now()
                fir.status = FurtherInformationRequest.RESPONDED
                fir.response_by = request.user
                fir.save()

                application.update_order_datetime()
                application.save()

                notify.further_information_responded(application, fir)

                return redirect(reverse("workbasket"))
        else:
            form = FurtherInformationRequestResponseForm(instance=fir)

    context = {
        "process": application,
        "fir": fir,
        "form": form,
        "case_type": case_type,
    }

    return render(request, "web/domains/case/respond-fir.html", context)
