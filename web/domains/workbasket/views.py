from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from guardian.shortcuts import get_objects_for_user

from web.domains.case._import.models import ImportApplication
from web.domains.case.access.approval.models import (
    ExporterApprovalRequest,
    ImporterApprovalRequest,
)
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
from web.domains.case.export.models import CertificateOfManufactureApplication
from web.domains.case.models import UpdateRequest
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.flow.models import Task


@login_required
def show_workbasket(request: HttpRequest) -> HttpResponse:
    if request.user.has_perm("web.reference_data_access"):
        qs = _get_queryset_admin(request.user)
    else:
        qs = _get_queryset_user(request.user)

    rows = [r.get_workbasket_row(request.user) for r in qs]

    context = {"rows": rows}

    return render(request, "web/domains/workbasket/workbasket.html", context)


def _get_queryset_admin(user: User) -> QuerySet:
    # TODO: why is this not getting all ExportApplication objects...?
    certificates = CertificateOfManufactureApplication.objects.filter(
        is_active=True
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    exporter_access_requests = ExporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    importer_access_requests = ImporterAccessRequest.objects.filter(
        is_active=True, status=AccessRequest.Statuses.SUBMITTED
    ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

    import_application = (
        ImportApplication.objects.filter(is_active=True)
        .exclude(update_requests__status__in=[UpdateRequest.OPEN, UpdateRequest.UPDATE_IN_PROGRESS])
        .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
    )

    return chain(
        certificates, exporter_access_requests, importer_access_requests, import_application
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

    # Import Application
    import_application = (
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

    # TODO: this is missing exportapplications

    return chain(
        exporter_approval_requests,
        importer_approval_requests,
        access_requests,
        import_application,
    )
