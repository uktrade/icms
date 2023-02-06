from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case.access.approval.forms import (
    ApprovalRequestResponseForm,
    ExporterApprovalRequestForm,
    ImporterApprovalRequestForm,
)
from web.domains.case.access.approval.models import (
    ApprovalRequest,
    ExporterApprovalRequest,
    ImporterApprovalRequest,
)
from web.domains.case.access.models import ExporterAccessRequest, ImporterAccessRequest
from web.domains.case.services import case_progress
from web.types import AuthenticatedHttpRequest


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def management_access_approval(
    request: AuthenticatedHttpRequest, *, pk: int, entity: str
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=pk
            )
            Form = ImporterApprovalRequestForm
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=pk
            )
            Form = ExporterApprovalRequestForm

        case_progress.access_request_in_processing(application)

        try:
            approval_request = application.approval_requests.get(is_active=True)
        except ApprovalRequest.DoesNotExist:
            approval_request = None

        if request.method == "POST":
            form = Form(application, data=request.POST)
            if form.is_valid():
                approval_request = form.save(commit=False)

                approval_request.status = ApprovalRequest.OPEN
                approval_request.access_request = application
                approval_request.requested_by = request.user
                approval_request.save()

                # TODO: Approval Request is missing email template from Oracle db
                # to notify importer's or exporter's contacts of the request

                return redirect(
                    reverse(
                        "access:case-management-access-approval",
                        kwargs={"pk": application.pk, "entity": entity},
                    )
                )
        else:
            form = Form(application, instance=approval_request)

        context = {
            "case_type": "access",
            "process": application,
            "form": form,
            "approval_request": approval_request,
            "entity": entity,
        }

    return render(
        request=request,
        template_name="web/domains/case/access/management-access-approval.html",
        context=context,
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def management_access_approval_withdraw(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str, approval_request_pk: int
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )

        approval_request = get_object_or_404(
            application.approval_requests.filter(is_active=True).select_for_update(),
            pk=approval_request_pk,
        )

        case_progress.access_request_in_processing(application)

        approval_request.is_active = False
        approval_request.status = ApprovalRequest.CANCELLED
        approval_request.save()

        return redirect(
            reverse(
                "access:case-management-access-approval",
                kwargs={"pk": application.pk, "entity": entity},
            )
        )


@login_required
@require_POST
def take_ownership_approval(
    request: AuthenticatedHttpRequest, *, pk: int, entity: str
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=pk
            )
            group_permission = "web.importer_access"
            permission = "web.is_contact_of_importer"
            link = application.access_request.importeraccessrequest.link
        else:
            application = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=pk
            )
            group_permission = "web.exporter_access"
            permission = "web.is_contact_of_exporter"
            link = application.access_request.exporteraccessrequest.link

        case_progress.access_request_in_processing(application)

        if not request.user.has_perm(group_permission):
            raise PermissionDenied

        if not request.user.has_perm(permission, link):
            raise PermissionDenied

        application.requested_from = request.user
        application.save()

    return redirect(reverse("workbasket"))


@login_required
@require_POST
def release_ownership_approval(
    request: AuthenticatedHttpRequest, *, pk: int, entity: str
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=pk
            )
            group_permission = "web.importer_access"
            permission = "web.is_contact_of_importer"
            link = application.access_request.importeraccessrequest.link
        else:
            application = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=pk
            )
            group_permission = "web.exporter_access"
            permission = "web.is_contact_of_exporter"
            link = application.access_request.exporteraccessrequest.link

        case_progress.access_request_in_processing(application)

        if not request.user.has_perm(group_permission):
            raise PermissionDenied

        if not request.user.has_perm(permission, link):
            raise PermissionDenied

        application = get_object_or_404(ApprovalRequest.objects.select_for_update(), pk=pk)
        application.requested_from = None
        application.save()

    return redirect(reverse("workbasket"))


@login_required
def case_approval_respond(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str, approval_request_pk: int
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
            approval = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )
            group_permission = "web.importer_access"
            permission = "web.is_contact_of_importer"
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
            approval = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )
            group_permission = "web.exporter_access"
            permission = "web.is_contact_of_exporter"

        if not request.user.has_perm(group_permission):
            raise PermissionDenied

        if not request.user.has_perm(permission, application.link):
            raise PermissionDenied

        case_progress.access_request_in_processing(application)

        if request.method == "POST":
            form = ApprovalRequestResponseForm(request.POST, instance=approval)
            if form.is_valid():
                approval = form.save(commit=False)
                approval.status = ApprovalRequest.COMPLETED
                approval.response_date = timezone.now()
                approval.response_by = request.user
                approval.save()

                return redirect(reverse("workbasket"))

        else:
            form = ApprovalRequestResponseForm(instance=approval)

    context = {"process": application, "form": form, "entity": entity, "approval": approval}
    return render(request, "web/domains/case/access/case-approval-respond.html", context)
