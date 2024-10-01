from itertools import chain
from typing import Literal

from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Exists, F, Func, OuterRef, Q, QuerySet, Subquery, Value
from guardian.shortcuts import get_objects_for_user

from web.domains.case.shared import ImpExpStatus
from web.flow.models import ProcessTypes
from web.mail.constants import CaseEmailCodes
from web.models import (
    AccessRequest,
    ApprovalRequest,
    CaseEmail,
    ExportApplication,
    Exporter,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    FurtherInformationRequest,
    ImportApplication,
    Importer,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    Mailshot,
    Task,
    UpdateRequest,
    User,
    WithdrawApplication,
)
from web.permissions import Perms

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


def get_caseworker_app_filters(user: User) -> tuple[Q, ...]:
    """Common caseworker application filter for workbasket rows"""

    return (
        #
        # Active applications
        Q(is_active=True),
        #
        # Active application types
        Q(application_type__is_active=True),
        #
        # Status filter
        (
            # Cases managed by user
            (
                Q(case_owner=user)
                & Q(status__in=[ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED])
            )
            # Or managed by user and is currently being revoked.
            | (
                Q(case_owner=user)
                & Q(status=ImpExpStatus.REVOKED)
                & (
                    Q(tasks__is_active=True)
                    & Q(
                        tasks__task_type__in=[
                            Task.TaskType.CHIEF_WAIT,
                            Task.TaskType.CHIEF_REVOKE_WAIT,
                        ]
                    )
                )
            )
            # Or cases up for grabs by any caseworker
            | (
                Q(case_owner__isnull=True)
                & Q(status__in=[ImpExpStatus.SUBMITTED, ImpExpStatus.VARIATION_REQUESTED])
            )
        ),
    )


# Applicant statuses to show
APP_STATUS_TO_SHOW = [
    ImpExpStatus.IN_PROGRESS,
    ImpExpStatus.SUBMITTED,
    ImpExpStatus.PROCESSING,
    ImpExpStatus.VARIATION_REQUESTED,
    ImpExpStatus.COMPLETED,
    ImpExpStatus.REVOKED,
    #
    # Statuses excluded:
    # ImpExpStatus.STOPPED,
    # ImpExpStatus.WITHDRAWN,
    # ImpExpStatus.DELETED,
]


def get_ilb_admin_qs(user: User) -> chain[QuerySet]:
    submitted = AccessRequest.Statuses.SUBMITTED

    # Annotations used on every row to improve performance
    open_fir_pks_annotation = _get_open_firs_pk_annotation("further_information_requests")

    exporter_access_requests = (
        ExporterAccessRequest.objects.filter(is_active=True, status=submitted)
        .annotate(
            annotation_open_fir_pks=open_fir_pks_annotation,
            annotation_has_open_approval_request=_get_approval_request_annotation(
                ExporterApprovalRequest, ApprovalRequest.Statuses.OPEN
            ),
            annotation_has_complete_approval_request=_get_approval_request_annotation(
                ExporterApprovalRequest, ApprovalRequest.Statuses.COMPLETED
            ),
        )
        .select_related("submitted_by")
    )

    importer_access_requests = (
        ImporterAccessRequest.objects.filter(is_active=True, status=submitted)
        .annotate(
            annotation_open_fir_pks=open_fir_pks_annotation,
            annotation_has_open_approval_request=_get_approval_request_annotation(
                ImporterApprovalRequest, ApprovalRequest.Statuses.OPEN
            ),
            annotation_has_complete_approval_request=_get_approval_request_annotation(
                ImporterApprovalRequest, ApprovalRequest.Statuses.COMPLETED
            ),
        )
        .select_related("submitted_by")
    )

    app_filters = get_caseworker_app_filters(user=user)

    export_applications = (
        ExportApplication.objects.filter(*app_filters)
        .exclude(decision=ExportApplication.REFUSE)
        .select_related("exporter", "contact", "application_type", "submitted_by", "case_owner")
        .annotate(
            annotation_has_withdrawal=EXPORT_HAS_WITHDRAWAL_ANNOTATION,
            active_tasks=ACTIVE_TASK_ANNOTATION,
            annotation_open_fir_pks=open_fir_pks_annotation,
            open_case_emails=_get_open_case_emails_annotation("export_applications"),
        )
    )

    import_applications = (
        ImportApplication.objects.filter(*app_filters)
        .exclude(decision=ImportApplication.REFUSE)
        .select_related("importer", "contact", "application_type", "submitted_by", "case_owner")
        .annotate(
            active_tasks=ACTIVE_TASK_ANNOTATION,
            annotation_has_withdrawal=IMPORT_HAS_WITHDRAWAL_ANNOTATION,
            annotation_open_fir_pks=open_fir_pks_annotation,
            open_case_emails=_get_open_case_emails_annotation("import_applications"),
        )
    )

    return chain(
        exporter_access_requests,
        importer_access_requests,
        export_applications,
        import_applications,
    )


def _get_open_case_emails_annotation(
    related_name: Literal["import_applications", "export_applications"]
) -> Subquery:

    return ArraySubquery(
        CaseEmail.objects.filter(
            status=CaseEmail.Status.OPEN,
            template_code__in=[
                CaseEmailCodes.BEIS_CASE_EMAIL,
                CaseEmailCodes.CONSTABULARY_CASE_EMAIL,
                CaseEmailCodes.HSE_CASE_EMAIL,
                CaseEmailCodes.SANCTIONS_CASE_EMAIL,
            ],
            is_active=True,
            **{related_name: OuterRef("pk")},
        )
        .values("template_code")
        .distinct("template_code")
    )


def _get_approval_request_annotation(
    approval_cls: type[ExporterApprovalRequest | ImporterApprovalRequest],
    status: ApprovalRequest.Statuses,
) -> Subquery:
    return Exists(approval_cls.objects.filter(access_request=OuterRef("pk"), status=status))


def get_sanctions_case_officer_qs(user: User) -> chain[QuerySet]:
    app_filters = get_caseworker_app_filters(user)
    # Annotations used on every row to improve performance
    open_fir_pks_annotation = _get_open_firs_pk_annotation("further_information_requests")

    import_applications = (
        ImportApplication.objects.filter(*app_filters, process_type=ProcessTypes.SANCTIONS)
        .exclude(decision=ImportApplication.REFUSE)
        .select_related("importer", "contact", "application_type", "submitted_by", "case_owner")
        .annotate(
            active_tasks=ACTIVE_TASK_ANNOTATION,
            annotation_has_withdrawal=IMPORT_HAS_WITHDRAWAL_ANNOTATION,
            annotation_open_fir_pks=open_fir_pks_annotation,
            open_case_emails=_get_open_case_emails_annotation("import_applications"),
        )
    )

    return chain(import_applications)


def get_applicant_qs(user: User) -> chain[QuerySet]:
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

    # User access requests
    chain_items = [access_requests]

    # Importer applications and approval requests
    if user.has_perm(Perms.sys.importer_access):
        chain_items.extend(_get_importer_queryset(user))

    # Exporter applications and approval requests.
    if user.has_perm(Perms.sys.exporter_access):
        chain_items.extend(_get_exporter_queryset(user))

    return chain(*chain_items)


def _get_importer_queryset(user: User) -> list[QuerySet]:
    open_fir_pks_annotation = _get_open_firs_pk_annotation(
        "access_request__further_information_requests"
    )

    main_importers = get_objects_for_user(
        user,
        [
            Perms.obj.importer.view,
            Perms.obj.importer.edit,
            Perms.obj.importer.manage_contacts_and_agents,
        ],
        Importer.objects.filter(is_active=True, main_importer__isnull=True),
        any_perm=True,
    )

    agent_importers = get_objects_for_user(
        user,
        [Perms.obj.importer.view, Perms.obj.importer.edit],
        Importer.objects.filter(is_active=True, main_importer__isnull=False),
        any_perm=True,
    )

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
            status=ApprovalRequest.Statuses.OPEN,
            access_request__importeraccessrequest__link__in=main_importers,
        )
    )

    # Import Applications
    import_applications = ImportApplication.objects.select_related(
        "importer", "contact", "application_type", "submitted_by"
    )
    # Add annotations
    import_applications = _add_user_import_annotations(import_applications)

    import_applications = (
        import_applications.filter(is_active=True, status__in=APP_STATUS_TO_SHOW)
        .filter(
            # Has permission at main org and there is no agent specified
            (Q(importer__in=main_importers) & Q(agent__isnull=True))
            # or
            |
            # Has permission at main org and there is an agent specified and the app is complete
            (
                Q(importer__in=main_importers)
                & Q(agent__isnull=False)
                & Q(status=ImpExpStatus.COMPLETED)
            )
            # or
            |
            # Has permission at the agent directly (agent contacts)
            (Q(agent__in=agent_importers))
        )
        .exclude(cleared_by=user)
    )

    # These annotations are required to work with other workbasket code.
    # Prior to mailshots, all workbasket rows derived from class Process
    mailshots = (
        Mailshot.objects.filter(
            is_active=True, status=Mailshot.Statuses.PUBLISHED, is_to_importers=True
        )
        .annotate(order_datetime=F("published_datetime"), process_type=Value("MAILSHOT"))
        .exclude(cleared_by=user)
    )

    return [importer_approval_requests, import_applications, mailshots]


def _get_exporter_queryset(user: User) -> list[QuerySet]:
    open_fir_pks_annotation = _get_open_firs_pk_annotation(
        "access_request__further_information_requests"
    )
    main_exporters = get_objects_for_user(
        user,
        [
            Perms.obj.exporter.view,
            Perms.obj.exporter.edit,
            Perms.obj.exporter.manage_contacts_and_agents,
        ],
        Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
        any_perm=True,
    )

    agent_exporters = get_objects_for_user(
        user,
        [Perms.obj.exporter.view, Perms.obj.exporter.edit],
        Exporter.objects.filter(is_active=True, main_exporter__isnull=False),
        any_perm=True,
    )

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
            status=ApprovalRequest.Statuses.OPEN,
            access_request__exporteraccessrequest__link__in=main_exporters,
        )
    )

    # Export Applications
    export_applications = ExportApplication.objects.select_related(
        "exporter", "contact", "application_type", "submitted_by"
    )
    # Add annotations
    export_applications = _add_user_export_annotations(export_applications)

    # Apply filters
    export_applications = (
        export_applications.filter(is_active=True, status__in=APP_STATUS_TO_SHOW)
        .filter(
            # Has permission at main org and there is no agent specified
            (Q(exporter__in=main_exporters) & Q(agent__isnull=True))
            # or
            |
            # Has permission at main org and there is an agent specified and the app is complete
            (
                Q(exporter__in=main_exporters)
                & Q(agent__isnull=False)
                & Q(status=ImpExpStatus.COMPLETED)
            )
            # or
            |
            # Has permission at the agent directly (agent contacts)
            (Q(agent__in=agent_exporters))
        )
        .exclude(cleared_by=user)
    )

    # These annotations are required to work with other workbasket code.
    # Prior to mailshots, all workbasket rows derived from class Process
    mailshots = (
        Mailshot.objects.filter(
            is_active=True, status=Mailshot.Statuses.PUBLISHED, is_to_exporters=True
        )
        .annotate(order_datetime=F("published_datetime"), process_type=Value("MAILSHOT"))
        .exclude(cleared_by=user)
    )

    return [exporter_approval_requests, export_applications, mailshots]


def _add_user_import_annotations(
    applications: QuerySet[ImportApplication],
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
        filter=Q(
            **{
                "update_requests__status": UpdateRequest.Status.OPEN,
                "update_requests__is_active": True,
            }
        ),
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
    applications: QuerySet[ExportApplication],
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
        filter=Q(
            **{
                "update_requests__status": UpdateRequest.Status.OPEN,
                "update_requests__is_active": True,
            }
        ),
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
