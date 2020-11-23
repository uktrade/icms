from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case.access.approval.forms import (
    ExporterApprovalRequestForm,
    ImporterApprovalRequestForm,
)
from web.domains.case.access.approval.models import ApprovalRequest
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
from web.flow.models import Task


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def management_access_approval(request, pk, entity):
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
        task = application.get_task(AccessRequest.SUBMITTED, "request")

        try:
            approval_request = application.approval_requests.get(is_active=True)
        except ApprovalRequest.DoesNotExist:
            approval_request = None

        if request.POST:
            form = Form(application, data=request.POST)
            if form.is_valid():

                approval_request = form.save()

                approval_request.status = ApprovalRequest.OPEN
                approval_request.access_request = application
                approval_request.requested_by = request.user
                approval_request.save()

                task = Task.objects.create(
                    process=approval_request,
                    task_type="notify_contacts",
                    owner=approval_request.requested_from,
                )

                # TODO: Approval Request is missing email template from Oracle db
                # to notify importer's or exporter's contacts of the request

                # if requested_from has a user, give them ownership
                if approval_request.requested_from:
                    task.is_active = False
                    task.finished = timezone.now()
                    task.save()

                    Task.objects.create(
                        process=approval_request,
                        task_type="respond",
                        owner=approval_request.requested_from,
                        previous=task,
                    )

                return redirect(
                    reverse(
                        "access:case-management-access-approval",
                        kwargs={"pk": application.pk, "entity": entity},
                    )
                )
        else:
            form = Form(application, instance=approval_request)

        context = {
            "object": application,
            "task": task,
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
@permission_required("web.reference_data_access", raise_exception=True)
def management_access_approval_withdraw(request, application_pk, entity, approval_request_pk):
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

        application.get_task(AccessRequest.SUBMITTED, "request")

        approval_request.is_active = False
        approval_request.status = ApprovalRequest.CANCELLED
        approval_request.save()

        # Approval Request can be withdrawn after the task has been completed
        # TODO: check if needed
        try:
            approval_request_task = approval_request.get_task(
                ApprovalRequest.OPEN, "notify_contacts"
            )
        except Exception:
            pass
        else:
            approval_request_task.is_active = False
            approval_request_task.finished = timezone.now()
            approval_request_task.save()

        return redirect(
            reverse(
                "access:case-management-access-approval",
                kwargs={"pk": application.pk, "entity": entity},
            )
        )


@login_required
@require_POST
def take_ownership_approval(request, pk, entity):
    # TODO: ApprovalRequest user
    pass


@login_required
@require_POST
def release_ownership_approval(request, pk, entity):
    # TODO: ApprovalRequest user
    pass


@login_required
def case_approval_respond(request, application_pk, entity, approval_request_pk):
    # TODO: ApprovalRequest user
    pass
