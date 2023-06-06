from itertools import chain
from operator import attrgetter

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.core.paginator import Paginator
from django.db.models import Exists, F, Func, OuterRef, Q, QuerySet, Subquery, Value
from django.http.response import HttpResponse
from django.shortcuts import render
from guardian.shortcuts import get_objects_for_user

from web.domains.case.shared import ImpExpStatus
from web.models import (
    AccessRequest,
    ApprovalRequest,
    ExportApplication,
    Exporter,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    FurtherInformationRequest,
    ImportApplication,
    Importer,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    UpdateRequest,
    User,
    WithdrawApplication,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from .row import get_workbasket_row_func


@login_required
def show_workbasket(request: AuthenticatedHttpRequest) -> HttpResponse:
    is_ilb_admin = request.user.has_perm(Perms.sys.ilb_admin)

    if is_ilb_admin:
        qs_list = list(_get_queryset_admin(request.user))
    else:
        qs_list = list(_get_queryset_user(request.user))

    # Order all records before pagination
    qs_list.sort(key=attrgetter("order_datetime"), reverse=True)

    paginator = Paginator(qs_list, settings.WORKBASKET_PER_PAGE)
    page_number = request.GET.get("page", default=1)

    page_obj = paginator.get_page(page_number)

    # Only call get_workbasket_row on the row's being rendered
    rows = []

    for r in page_obj:
        get_workbasket_row = get_workbasket_row_func(r.process_type)
        row = get_workbasket_row(r, request.user, is_ilb_admin)

        rows.append(row)

    context = {"rows": rows, "page_obj": page_obj}

    return render(request, "web/domains/workbasket/workbasket.html", context)


# Used to get a list of active tasks for the application
# Prevents a call to get_active_task_list for every application record.
ACTIVE_TASK_ANNOTATION = ArrayAgg(
    "tasks__task_type", distinct=True, filter=Q(tasks__is_active=True), default=Value([])
)


IMPORT_HAS_WITHDRAWAL_ANNOTATION = Exists(
    WithdrawApplication.objects.filter(
        import_application=OuterRef("pk"),
        status=WithdrawApplication.Statuses.OPEN,
        is_active=True,
    )
)


EXPORT_HAS_WITHDRAWAL_ANNOTATION = Exists(
    WithdrawApplication.objects.filter(
        export_application=OuterRef("pk"),
        status=WithdrawApplication.Statuses.OPEN,
        is_active=True,
    )
)


def _get_queryset_admin(user: User) -> chain[QuerySet]:
    submitted = AccessRequest.Statuses.SUBMITTED

    # Annotations used on every row to improve performance
    open_fir_pks_annotation = _get_open_firs_pk_annotation("further_information_requests")

    open_exporter_approval_requests = Exists(
        ExporterApprovalRequest.objects.filter(access_request=OuterRef("pk"))
    )
    open_importer_approval_requests = Exists(
        ImporterApprovalRequest.objects.filter(access_request=OuterRef("pk"))
    )

    exporter_access_requests = (
        ExporterAccessRequest.objects.filter(is_active=True, status=submitted)
        .annotate(
            annotation_open_fir_pks=open_fir_pks_annotation,
            annotation_has_open_approval_request=open_exporter_approval_requests,
        )
        .select_related("submitted_by")
    )

    importer_access_requests = (
        ImporterAccessRequest.objects.filter(is_active=True, status=submitted)
        .annotate(
            annotation_open_fir_pks=open_fir_pks_annotation,
            annotation_has_open_approval_request=open_importer_approval_requests,
        )
        .select_related("submitted_by")
    )

    export_applications = (
        ExportApplication.objects.filter(is_active=True)
        .exclude(status=ImpExpStatus.STOPPED)
        .exclude(decision=ExportApplication.REFUSE)
        .select_related("exporter", "contact", "application_type", "submitted_by", "case_owner")
        .annotate(
            annotation_has_withdrawal=EXPORT_HAS_WITHDRAWAL_ANNOTATION,
            active_tasks=ACTIVE_TASK_ANNOTATION,
        )
    )

    import_applications = (
        ImportApplication.objects.filter(is_active=True)
        .exclude(status=ImpExpStatus.STOPPED)
        .exclude(decision=ImportApplication.REFUSE)
        .select_related("importer", "contact", "application_type", "submitted_by", "case_owner")
        .annotate(
            active_tasks=ACTIVE_TASK_ANNOTATION,
            annotation_has_withdrawal=IMPORT_HAS_WITHDRAWAL_ANNOTATION,
        )
    )

    return chain(
        exporter_access_requests,
        importer_access_requests,
        export_applications,
        import_applications,
    )


def _get_queryset_user(user: User) -> chain[QuerySet]:
    open_fir_pks_annotation = _get_open_firs_pk_annotation(
        "access_request__further_information_requests"
    )
    active_exporters = Exporter.objects.filter(is_active=True, main_exporter=None)

    # TODO: ICMSLST-1947 Revisit when updating workbasket / adding tests
    exporters = get_objects_for_user(
        user,
        [
            Perms.obj.exporter.view,
            Perms.obj.exporter.edit,
            Perms.obj.exporter.manage_contacts_and_agents,
        ],
        active_exporters,
    )
    exporters_managed_by_agents = get_objects_for_user(
        user,
        [Perms.obj.exporter.is_agent],
        active_exporters,
    )

    active_importers = Importer.objects.filter(is_active=True, main_importer=None)

    # TODO: ICMSLST-1947 Revisit when updating workbasket / adding tests
    importers = get_objects_for_user(
        user,
        [
            Perms.obj.importer.view,
            Perms.obj.importer.edit,
            Perms.obj.importer.manage_contacts_and_agents,
        ],
        active_importers,
    )
    importers_managed_by_agents = get_objects_for_user(
        user,
        [Perms.obj.importer.is_agent],
        active_importers,
    )

    # TODO ICMSLST-873: check if agent's contacts can do Approval Request
    exporter_approval_requests = (
        ExporterApprovalRequest.objects.select_related(
            # get the exporter associated with the approval request
            # join access_request and join exporter from access_request
            "access_request__exporteraccessrequest__link",
            "access_request__submitted_by",
        )
        .annotate(annotation_open_fir_pks=open_fir_pks_annotation)
        .filter(
            is_active=True,
            status=ApprovalRequest.OPEN,
            access_request__exporteraccessrequest__link__in=exporters,
        )
    )

    # TODO ICMSLST-873: check if agent's contacts can do Approval Request
    importer_approval_requests = (
        ImporterApprovalRequest.objects.select_related(
            # get the importer associated with the approval request
            # join access_request and join importer from access_request
            "access_request__importeraccessrequest__link",
            "access_request__submitted_by",
        )
        .annotate(annotation_open_fir_pks=open_fir_pks_annotation)
        .filter(
            is_active=True,
            status=ApprovalRequest.OPEN,
            access_request__importeraccessrequest__link__in=importers,
        )
    )

    # user/admin access requests and firs
    open_fir_pks_annotation = _get_open_firs_pk_annotation("further_information_requests")

    access_requests = (
        AccessRequest.objects.filter(
            submitted_by_id=user.pk,
            status__in=[AccessRequest.Statuses.SUBMITTED, AccessRequest.Statuses.FIR_REQUESTED],
        )
        .select_related("submitted_by")
        .annotate(annotation_open_fir_pks=open_fir_pks_annotation)
    )

    # Import Applications
    import_applications = ImportApplication.objects.all().select_related(
        "importer", "contact", "application_type", "submitted_by"
    )

    # Add annotations
    import_applications = _add_user_import_annotations(import_applications)

    # Apply filters
    # TODO: I'm not sure why we are filtering on state.
    # When its being processed by the admin (PROCESSING state) the "view" link should still show.
    app_status_to_show = [
        ImpExpStatus.COMPLETED,
        ImpExpStatus.SUBMITTED,
        ImpExpStatus.IN_PROGRESS,
        ImpExpStatus.PROCESSING,
        ImpExpStatus.VARIATION_REQUESTED,
        ImpExpStatus.REVOKED,
    ]
    import_applications = import_applications.filter(
        is_active=True, status__in=app_status_to_show
    ).filter(
        # Either applications managed by contacts of importer
        (
            Q(importer__in=importers.exclude(pk__in=importers_managed_by_agents))
            & Q(agent__isnull=True)
        )
        # or applications managed by agents
        | (Q(importer__in=importers_managed_by_agents) & Q(agent__isnull=False))
    )

    # Export Applications
    export_applications = ExportApplication.objects.all().select_related(
        "exporter", "contact", "application_type", "submitted_by"
    )

    # Add annotations
    export_applications = _add_user_export_annotations(export_applications)

    # Apply filters
    export_applications = export_applications.filter(
        is_active=True, status__in=app_status_to_show
    ).filter(
        # Either applications managed by contacts of exporter
        (
            Q(exporter__in=exporters.exclude(pk__in=exporters_managed_by_agents))
            & Q(agent__isnull=True)
        )
        # or applications managed by agents
        | (Q(exporter__in=exporters_managed_by_agents) & Q(agent__isnull=False))
    )

    return chain(
        exporter_approval_requests,
        importer_approval_requests,
        access_requests,
        import_applications,
        export_applications,
    )


def _add_user_import_annotations(
    applications: "QuerySet[ImportApplication]",
) -> "QuerySet[ImportApplication]":
    """Add user workbasket annotations for import applications."""

    open_fir_subquery = (
        FurtherInformationRequest.objects.filter(
            importapplication=OuterRef("pk"),
            status=FurtherInformationRequest.OPEN,
        )
        .order_by()
        .values("importapplication")
        .annotate(
            open_fir_pairs_annotation=JSONBAgg(
                Func(F("pk"), F("requested_datetime"), function="json_build_array"),
                ordering="requested_datetime",
            )
        )
        .values("open_fir_pairs_annotation")
    )

    open_ur_pks_annotation = ArrayAgg(
        "update_requests__pk",
        distinct=True,
        filter=Q(**{"update_requests__status": UpdateRequest.Status.OPEN, "is_active": True}),
        default=Value([]),
    )

    has_in_progress_ur = Exists(
        UpdateRequest.objects.filter(
            importapplication=OuterRef("pk"),
            status__in=[UpdateRequest.Status.UPDATE_IN_PROGRESS, UpdateRequest.Status.RESPONDED],
            is_active=True,
        )
    )

    return applications.annotate(
        active_tasks=ACTIVE_TASK_ANNOTATION,
        annotation_has_withdrawal=IMPORT_HAS_WITHDRAWAL_ANNOTATION,
        annotation_open_fir_pairs=Subquery(open_fir_subquery.values("open_fir_pairs_annotation")),
        annotation_open_ur_pks=open_ur_pks_annotation,
        annotation_has_in_progress_ur=has_in_progress_ur,
    )


def _add_user_export_annotations(
    applications: "QuerySet[ExportApplication]",
) -> "QuerySet[ExportApplication]":
    """Add user workbasket annotations for export applications."""

    open_fir_subquery = (
        FurtherInformationRequest.objects.filter(
            exportapplication=OuterRef("pk"),
            status=FurtherInformationRequest.OPEN,
        )
        .order_by()
        .values("exportapplication")
        .annotate(
            open_fir_pairs_annotation=JSONBAgg(
                Func(F("pk"), F("requested_datetime"), function="json_build_array"),
                ordering="requested_datetime",
            )
        )
        .values("open_fir_pairs_annotation")
    )

    open_ur_pks_annotation = ArrayAgg(
        "update_requests__pk",
        distinct=True,
        filter=Q(**{"update_requests__status": UpdateRequest.Status.OPEN, "is_active": True}),
        default=Value([]),
    )

    has_in_progress_ur = Exists(
        UpdateRequest.objects.filter(
            exportapplication=OuterRef("pk"),
            status__in=[UpdateRequest.Status.UPDATE_IN_PROGRESS, UpdateRequest.Status.RESPONDED],
            is_active=True,
        )
    )

    return applications.annotate(
        active_tasks=ACTIVE_TASK_ANNOTATION,
        annotation_has_withdrawal=EXPORT_HAS_WITHDRAWAL_ANNOTATION,
        annotation_open_fir_pairs=Subquery(open_fir_subquery.values("open_fir_pairs_annotation")),
        annotation_open_ur_pks=open_ur_pks_annotation,
        annotation_has_in_progress_ur=has_in_progress_ur,
    )


def _get_open_firs_pk_annotation(relationship: str) -> ArrayAgg:
    return ArrayAgg(
        f"{relationship}__pk",
        filter=Q(**{f"{relationship}__status": FurtherInformationRequest.OPEN}),
        ordering=f"{relationship}__requested_datetime",
        default=Value([]),
    )
