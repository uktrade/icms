from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, QuerySet
from django.http.response import HttpResponse
from django.shortcuts import render
from guardian.shortcuts import get_objects_for_user

from web.models import (
    AccessRequest,
    ExportApplication,
    Exporter,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    ImportApplication,
    Importer,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    Task,
    UpdateRequest,
    User,
)
from web.types import AuthenticatedHttpRequest


@login_required
def show_workbasket(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.user.has_perm("web.reference_data_access"):
        qs = _get_queryset_admin(request.user)
    else:
        qs = _get_queryset_user(request.user)

    rows = [r.get_workbasket_row(request.user) for r in qs]

    context = {"rows": rows}

    return render(request, "web/domains/workbasket/workbasket.html", context)


def _get_queryset_admin(user: User) -> QuerySet:
    exporter_access_requests = ExporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    importer_access_requests = ImporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    export_applications = (
        ExportApplication.objects.filter(is_active=True)
        .exclude(update_requests__status__in=[UpdateRequest.OPEN, UpdateRequest.UPDATE_IN_PROGRESS])
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
    )

    import_applications = (
        ImportApplication.objects.filter(is_active=True)
        .exclude(update_requests__status__in=[UpdateRequest.OPEN, UpdateRequest.UPDATE_IN_PROGRESS])
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
    )

    return chain(
        exporter_access_requests,
        importer_access_requests,
        export_applications,
        import_applications,
    )


def _get_queryset_user(user: User) -> QuerySet:
    # current user's exporters
    # TODO: check if agent's contacts can do Approval Request
    exporters = get_objects_for_user(user, ["is_contact_of_exporter"], Exporter)

    # current user's importers
    # TODO: check if agent's contacts can do Approval Request
    importers = get_objects_for_user(user, ["is_contact_of_importer"], Importer)

    exporter_approval_requests = (
        ExporterApprovalRequest.objects.select_related(
            # get the exporter associated with the approval request
            # join access_request and join exporter from access_request
            "access_request__exporteraccessrequest__link",
        )
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
        .filter(is_active=True)
        .filter(access_request__exporteraccessrequest__link__in=exporters)
    )

    importer_approval_requests = (
        ImporterApprovalRequest.objects.select_related(
            # get the importer associated with the approval request
            # join access_request and join importer from access_request
            "access_request__importeraccessrequest__link",
        )
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
        .filter(is_active=True)
        .filter(access_request__importeraccessrequest__link__in=importers)
    )

    # user/admin access requests and firs
    access_requests = (
        user.submitted_access_requests.filter(status=AccessRequest.Statuses.SUBMITTED)
        .prefetch_related("further_information_requests")
        .prefetch_related(
            Prefetch(
                "further_information_requests__tasks",
                queryset=Task.objects.filter(is_active=True, owner=user),
            )
        )
    )

    # Import Applications
    import_applications = (
        ImportApplication.objects.prefetch_related(
            Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
        )
        .filter(is_active=True)
        .filter(
            status__in=[
                ImportApplication.Statuses.SUBMITTED,
                ImportApplication.Statuses.IN_PROGRESS,
                ImportApplication.Statuses.WITHDRAWN,
                ImportApplication.Statuses.UPDATE_REQUESTED,
            ]
        )
        .filter(importer__in=importers)
    )

    # Export Applications
    export_applications = (
        ExportApplication.objects.prefetch_related(
            Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
        )
        .filter(is_active=True)
        .filter(
            status__in=[
                ExportApplication.Statuses.SUBMITTED,
                ExportApplication.Statuses.IN_PROGRESS,
                ExportApplication.Statuses.WITHDRAWN,
                ExportApplication.Statuses.UPDATE_REQUESTED,
            ]
        )
        .filter(exporter__in=exporters)
    )

    return chain(
        exporter_approval_requests,
        importer_approval_requests,
        access_requests,
        import_applications,
        export_applications,
    )
