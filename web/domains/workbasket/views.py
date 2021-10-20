from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q, QuerySet
from django.http.response import HttpResponse
from django.shortcuts import render
from guardian.shortcuts import get_objects_for_user

from web.domains.case.access.approval.models import ApprovalRequest
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
    User,
)
from web.types import AuthenticatedHttpRequest


@login_required
def show_workbasket(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.user.has_perm("web.ilb_admin"):
        qs = _get_queryset_admin(request.user)
    else:
        qs = _get_queryset_user(request.user)

    rows = [r.get_workbasket_row(request.user) for r in qs]

    context = {"rows": rows}

    return render(request, "web/domains/workbasket/workbasket.html", context)


def _get_queryset_admin(user: User) -> chain[QuerySet]:
    exporter_access_requests = ExporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    importer_access_requests = ImporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    export_applications = ExportApplication.objects.filter(is_active=True).prefetch_related(
        Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
    )

    import_applications = ImportApplication.objects.filter(is_active=True).prefetch_related(
        Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
    )

    return chain(
        exporter_access_requests,
        importer_access_requests,
        export_applications,
        import_applications,
    )


def _get_queryset_user(user: User) -> chain[QuerySet]:
    active_exporters = Exporter.objects.filter(is_active=True, main_exporter=None)
    exporters = get_objects_for_user(user, ["is_contact_of_exporter"], active_exporters)
    exporters_managed_by_agents = get_objects_for_user(
        user,
        ["web.is_agent_of_exporter"],
        active_exporters,
    )

    active_importers = Importer.objects.filter(is_active=True, main_importer=None)
    importers = get_objects_for_user(user, ["is_contact_of_importer"], active_importers)
    importers_managed_by_agents = get_objects_for_user(
        user,
        ["web.is_agent_of_importer"],
        active_importers,
    )

    # TODO ICMSLST-873: check if agent's contacts can do Approval Request
    exporter_approval_requests = (
        ExporterApprovalRequest.objects.select_related(
            # get the exporter associated with the approval request
            # join access_request and join exporter from access_request
            "access_request__exporteraccessrequest__link",
        )
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
        .filter(is_active=True)
        .filter(status=ApprovalRequest.OPEN)
        .filter(access_request__exporteraccessrequest__link__in=exporters)
    )

    # TODO ICMSLST-873: check if agent's contacts can do Approval Request
    importer_approval_requests = (
        ImporterApprovalRequest.objects.select_related(
            # get the importer associated with the approval request
            # join access_request and join importer from access_request
            "access_request__importeraccessrequest__link",
        )
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
        .filter(is_active=True)
        .filter(status=ApprovalRequest.OPEN)
        .filter(access_request__importeraccessrequest__link__in=importers)
    )

    # user/admin access requests and firs
    access_requests = (
        user.submitted_access_requests.filter(
            status__in=[AccessRequest.Statuses.SUBMITTED, AccessRequest.Statuses.FIR_REQUESTED]
        )
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
                ImportApplication.Statuses.COMPLETED,
                ImportApplication.Statuses.SUBMITTED,
                ImportApplication.Statuses.IN_PROGRESS,
            ]
        )
        .filter(
            # Either applications managed by contacts of importer
            (
                Q(importer__in=importers.exclude(pk__in=importers_managed_by_agents))
                & Q(agent__isnull=True)
            )
            # or applications managed by agents
            | (Q(importer__in=importers_managed_by_agents) & Q(agent__isnull=False))
            # or applications acknowledged by agents
            | (
                Q(importer__in=importers)
                & Q(agent__isnull=False)
                & Q(acknowledged_by__isnull=False)
            )
        )
    )

    # Export Applications
    export_applications = (
        ExportApplication.objects.prefetch_related(
            Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
        )
        .filter(is_active=True)
        .filter(
            status__in=[
                ExportApplication.Statuses.COMPLETED,
                ExportApplication.Statuses.SUBMITTED,
                ExportApplication.Statuses.IN_PROGRESS,
            ]
        )
        .filter(
            # Either applications managed by contacts of exporter
            (
                Q(exporter__in=exporters.exclude(pk__in=exporters_managed_by_agents))
                & Q(agent__isnull=True)
            )
            # or applications managed by agents
            | (Q(exporter__in=exporters_managed_by_agents) & Q(agent__isnull=False))
        )
    )

    return chain(
        exporter_approval_requests,
        importer_approval_requests,
        access_requests,
        import_applications,
        export_applications,
    )
