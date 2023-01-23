from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from guardian.shortcuts import get_users_with_perms

from web.domains.case.shared import ImpExpStatus
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.domains.user.models import User
from web.flow.models import ProcessTypes, Task
from web.notify import notify
from web.types import AuthenticatedHttpRequest

from .. import forms
from ..fir import forms as fir_forms
from ..fir.models import FurtherInformationRequest
from ..types import ImpOrExpOrAccess
from ..utils import (
    check_application_permission,
    get_application_current_task,
    get_case_page_title,
    view_application_file,
)
from .utils import get_class_imp_or_exp_or_access, get_current_task_and_readonly_status


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_firs(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        # Access requests don't have a case_owner so can't call get_current_task_and_readonly_status
        if application.process_type in [ProcessTypes.EAR, ProcessTypes.IAR]:
            get_application_current_task(
                application, case_type, Task.TaskType.PROCESS, select_for_update=False
            )
            readonly_view = False
        else:
            _, readonly_view = get_current_task_and_readonly_status(
                application, case_type, request.user, Task.TaskType.PROCESS
            )

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
            "firs": application.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ).filter(is_active=True),
            "case_type": case_type,
            "page_title": get_case_page_title(
                case_type, application, "Further Information Requests"
            ),
            "readonly_view": readonly_view,
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
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def add_fir(request, *, application_pk: int, case_type: str) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)

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

        fir = application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=template.get_title(title_mapping),
            request_detail=template.get_content(content_mapping),
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

    return redirect(
        reverse(
            "case:edit-fir",
            kwargs={"application_pk": application_pk, "fir_pk": fir.pk, "case_type": case_type},
        )
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_fir(request, *, application_pk: int, fir_pk: int, case_type: str) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
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

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        if request.method == "POST":
            form = fir_forms.FurtherInformationRequestForm(request.POST, instance=fir)

            if form.is_valid():
                fir = form.save()

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()

                    notify.further_information_requested(fir, contacts)

                    application.update_order_datetime()
                    application.save()

                return _manage_fir_redirect(application_pk, case_type)
        else:
            form = fir_forms.FurtherInformationRequestForm(instance=fir)

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
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def delete_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
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
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def withdraw_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def close_fir(
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:
    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

    return _manage_fir_redirect(application_pk, case_type)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
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
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)
        check_application_permission(application, request.user, case_type)

        fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

        if request.method == "POST":
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

    model_class = get_class_imp_or_exp_or_access(case_type)
    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)
    fir = get_object_or_404(application.further_information_requests, pk=fir_pk)

    return view_application_file(request.user, application, fir.files, file_pk, case_type)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
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
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, user, case_type)

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
    model_class = get_class_imp_or_exp_or_access(case_type)

    with transaction.atomic():
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, case_type)

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
    request: AuthenticatedHttpRequest, *, application_pk: int, fir_pk: int, case_type: str
) -> HttpResponse:

    with transaction.atomic():
        model_class = get_class_imp_or_exp_or_access(case_type)
        application: ImpOrExpOrAccess = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, case_type)
        application.check_expected_status(
            [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        )
        fir = get_object_or_404(application.further_information_requests.open(), pk=fir_pk)

        if request.method == "POST":
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir, data=request.POST)

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
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir)

    context = {
        "process": application,
        "fir": fir,
        "form": form,
        "case_type": case_type,
    }

    return render(request, "web/domains/case/respond-fir.html", context)
