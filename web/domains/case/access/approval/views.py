from typing import Literal

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
from web.domains.case.services import case_progress
from web.mail.emails import (
    send_approval_request_completed_email,
    send_approval_request_opened_email,
)
from web.models import (
    ApprovalRequest,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    ImporterAccessRequest,
    ImporterApprovalRequest,
)
from web.permissions import Perms, can_user_manage_org_contacts
from web.types import AuthenticatedHttpRequest


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_access_approval(
    request: AuthenticatedHttpRequest,
    *,
    access_request_pk: int,
    entity: Literal["importer", "exporter"],
) -> HttpResponse:
    """View to manage approval requests linked to an access request.

    An organisation must be linked before an approval request can be created.

    :param request: Django request object
    :param access_request_pk: primary key of the AccessRequest record
    :param entity: literal "importer" or "exporter" value
    """

    with transaction.atomic():
        if entity == "importer":
            model_cls = ImporterAccessRequest
            form_cls = ImporterApprovalRequestForm
        else:
            model_cls = ExporterAccessRequest
            form_cls = ExporterApprovalRequestForm

        access_request = get_object_or_404(
            model_cls.objects.select_for_update(), pk=access_request_pk
        )

        case_progress.access_request_in_processing(access_request)

        if request.method == "POST":
            form = form_cls(request.POST, access_request=access_request)

            if form.is_valid():
                approval_request = form.save(commit=False)
                approval_request.status = ApprovalRequest.Statuses.OPEN
                approval_request.access_request = access_request
                approval_request.requested_by = request.user
                approval_request.save()
                send_approval_request_opened_email(approval_request)
                return redirect(
                    reverse(
                        "access:case-management-access-approval",
                        kwargs={"access_request_pk": access_request.pk, "entity": entity},
                    )
                )
        else:
            approval_request = access_request.approval_requests.filter(is_active=True).first()
            form = form_cls(instance=approval_request, access_request=access_request)

        context = {
            "case_type": "access",
            "process": access_request,
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def manage_access_approval_withdraw(
    request: AuthenticatedHttpRequest,
    *,
    access_request_pk: int,
    entity: Literal["importer", "exporter"],
    approval_request_pk: int,
) -> HttpResponse:
    """View to withdraw an approval request linked to an access request.

    :param request: Django request object
    :param access_request_pk: primary key of the AccessRequest record
    :param entity: literal "importer" or "exporter" value
    :param approval_request_pk: Primary key of the ApprovalRequest record.
    """

    with transaction.atomic():
        model_cls = ImporterAccessRequest if entity == "importer" else ExporterAccessRequest
        access_request = get_object_or_404(model_cls, pk=access_request_pk)

        case_progress.access_request_in_processing(access_request)

        approval_request = get_object_or_404(
            access_request.approval_requests.filter(is_active=True).select_for_update(),
            pk=approval_request_pk,
        )

        approval_request.is_active = False
        approval_request.status = ApprovalRequest.Statuses.CANCELLED
        approval_request.save()

        return redirect(
            reverse(
                "access:case-management-access-approval",
                kwargs={"access_request_pk": access_request.pk, "entity": entity},
            )
        )


@login_required
@require_POST
def take_ownership_access_approval(
    request: AuthenticatedHttpRequest,
    *,
    approval_request_pk: int,
    entity: Literal["importer", "exporter"],
) -> HttpResponse:
    """View to take ownership of an approval request that needs approving or rejecting.

    :param request: Django request object
    :param approval_request_pk: Primary key of the ApprovalRequest record.
    :param entity: literal "importer" or "exporter" value
    """

    with transaction.atomic():
        if entity == "importer":
            approval_request = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )
        else:
            approval_request = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )

        case_progress.approval_request_in_processing(approval_request)

        # Already assigned
        if approval_request.requested_from:
            raise PermissionDenied

        org = approval_request.access_request.get_specific_model().link
        if not can_user_manage_org_contacts(request.user, org):
            raise PermissionDenied

        approval_request.requested_from = request.user
        approval_request.save()

    return redirect(
        reverse(
            "access:case-approval-respond",
            kwargs={
                "access_request_pk": approval_request.access_request.id,
                "entity": entity,
                "approval_request_pk": approval_request.pk,
            },
        )
    )


@login_required
@require_POST
def release_ownership_access_approval(
    request: AuthenticatedHttpRequest,
    *,
    approval_request_pk: int,
    entity: Literal["importer", "exporter"],
) -> HttpResponse:
    """View to release ownership of an approval request that needs approving or rejecting.

    :param request: Django request object
    :param approval_request_pk: Primary key of the ApprovalRequest record.
    :param entity: literal "importer" or "exporter" value
    """

    with transaction.atomic():
        if entity == "importer":
            approval_request = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )
        else:
            approval_request = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )

        case_progress.approval_request_in_processing(approval_request)

        if approval_request.requested_from != request.user:
            raise PermissionDenied

        org = approval_request.access_request.get_specific_model().link
        if not can_user_manage_org_contacts(request.user, org):
            raise PermissionDenied

        approval_request.requested_from = None
        approval_request.save()

    return redirect(reverse("workbasket"))


@login_required
def close_access_approval(
    request: AuthenticatedHttpRequest,
    *,
    access_request_pk: int,
    entity: str,
    approval_request_pk: int,
) -> HttpResponse:
    """View to either approve or refuse an approval request.

    This does nothing to the access request but informs the ILB admin if the access request should
    be approved or rejected.

    :param request: Django request object
    :param access_request_pk: primary key of the AccessRequest record
    :param entity: literal "importer" or "exporter" value
    :param approval_request_pk: Primary key of the ApprovalRequest record.
    """

    with transaction.atomic():
        if entity == "importer":
            access_request = get_object_or_404(ImporterAccessRequest, pk=access_request_pk)
            approval_request = get_object_or_404(
                ImporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )
        else:
            access_request = get_object_or_404(ExporterAccessRequest, pk=access_request_pk)
            approval_request = get_object_or_404(
                ExporterApprovalRequest.objects.select_for_update(), pk=approval_request_pk
            )

        case_progress.access_request_in_processing(access_request)

        if approval_request.requested_from != request.user:
            raise PermissionDenied

        if not can_user_manage_org_contacts(request.user, access_request.link):
            raise PermissionDenied

        if request.method == "POST":
            form = ApprovalRequestResponseForm(request.POST, instance=approval_request)

            if form.is_valid():
                approval_request = form.save(commit=False)
                approval_request.status = ApprovalRequest.Statuses.COMPLETED
                approval_request.response_date = timezone.now()
                approval_request.response_by = request.user
                approval_request.save()
                send_approval_request_completed_email(approval_request)
                return redirect(reverse("workbasket"))

        else:
            form = ApprovalRequestResponseForm(instance=approval_request)

    context = {
        "process": access_request,
        "form": form,
        "entity": entity,
        "approval": approval_request,
    }

    return render(request, "web/domains/case/access/case-approval-respond.html", context)
