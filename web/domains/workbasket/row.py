import functools
from typing import Protocol

from django.urls import reverse

from web.domains.case.types import ImpOrExp, ImpOrExpOrAccessOrApproval
from web.flow.models import ProcessTypes
from web.models import (
    AccessRequest,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    FurtherInformationRequest,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    Mailshot,
    User,
)
from web.utils import datetime_format

from .actions import get_workbasket_admin_sections, get_workbasket_applicant_sections
from .base import WorkbasketAction, WorkbasketRow, WorkbasketSection


class GetWorkbasketRow(Protocol):
    """The protocol documenting the get_workbasket_row interface"""

    def __call__(
        self, app: ImpOrExpOrAccessOrApproval, user: User, is_ilb_admin: bool
    ) -> WorkbasketRow: ...


@functools.cache
def get_workbasket_row_func(process_type: str) -> GetWorkbasketRow:
    match process_type:
        #
        # Import Applications
        #
        case (
            ProcessTypes.DEROGATIONS
            | ProcessTypes.FA_DFL
            | ProcessTypes.FA_OIL
            | ProcessTypes.FA_SIL
            | ProcessTypes.IRON_STEEL
            | ProcessTypes.OPT
            | ProcessTypes.SANCTIONS
            | ProcessTypes.SPS
            | ProcessTypes.TEXTILES
            | ProcessTypes.WOOD
        ):
            return _get_case_wb_row
        #
        # Export Applications
        #
        case ProcessTypes.COM | ProcessTypes.CFS | ProcessTypes.GMP:
            return _get_case_wb_row
        #
        # Access requests
        #
        case ProcessTypes.IAR | ProcessTypes.EAR:
            return _get_access_wb_row
        #
        # Approval requests
        #
        case ProcessTypes.ExpApprovalReq | ProcessTypes.ImpApprovalReq:
            return _get_approval_wb_row
        #
        # Mailshots
        #
        case "MAILSHOT":
            return get_mailshot_row  # type:ignore[return-value]

        case _:
            raise NotImplementedError(f"Unsupported process_type: {process_type}")


def _get_case_wb_row(app: ImpOrExp, user: User, is_ilb_admin: bool) -> WorkbasketRow:
    r = WorkbasketRow()
    r.id = app.id

    r.reference = app.get_reference()

    r.timestamp = app.submit_datetime or app.created

    r.status = app.get_status_display()

    if app.is_import_application():
        r.company = app.importer
        case_type = "import"
        r.subject = "\n".join(["Import Application", ProcessTypes(app.process_type).label])
    else:
        r.company = app.exporter
        case_type = "export"
        r.subject = "\n".join(["Certificate Application", ProcessTypes(app.process_type).label])

    r.company_agent = app.agent

    if is_ilb_admin:
        sections = get_workbasket_admin_sections(user=user, case_type=case_type, application=app)
    else:
        sections = get_workbasket_applicant_sections(
            user=user, case_type=case_type, application=app
        )

    for section in sections:
        r.sections.append(section)

    return r


def _get_access_wb_row(
    app: ImporterAccessRequest | ExporterAccessRequest, user: User, is_ilb_admin: bool
) -> WorkbasketRow:
    r = WorkbasketRow()
    r.id = app.id

    r.reference = app.reference

    r.subject = ProcessTypes(app.process_type).label

    r.company = app.organisation_name

    r.status = app.get_status_display()

    r.timestamp = app.submit_datetime or app.created

    info_rows = ["Access Request"]

    if app.annotation_open_fir_pks:
        info_rows.append("Further Information Requested")

    if is_ilb_admin and app.annotation_has_open_approval_request:
        info_rows.append("Approval Requested")

    if is_ilb_admin and app.annotation_has_complete_approval_request:
        info_rows.append("Approval Complete")

    information = "\n".join(info_rows)

    if is_ilb_admin:
        admin_actions: list[WorkbasketAction] = []

        if app.process_type == ProcessTypes.EAR:
            entity = "exporter"
        elif app.process_type == ProcessTypes.IAR:
            entity = "importer"
        else:
            raise NotImplementedError(f"process_type: {app.process_type} not supported")

        admin_actions.append(
            WorkbasketAction(
                is_post=False,
                name="Manage",
                url=reverse(
                    "access:link-request", kwargs={"access_request_pk": app.pk, "entity": entity}
                ),
            ),
        )

        r.sections.append(WorkbasketSection(information=information, actions=admin_actions))

    if app.submitted_by == user:
        owner_actions: list[WorkbasketAction] = [
            WorkbasketAction(
                is_post=False,
                name="View",
                url=reverse("case:view", kwargs={"application_pk": app.pk, "case_type": "access"}),
                section_label="Access Request",
            )
        ]

        for fir_pk in app.annotation_open_fir_pks:
            kwargs = {"application_pk": app.pk, "fir_pk": fir_pk, "case_type": "access"}
            fir = FurtherInformationRequest.objects.get(pk=fir_pk)
            requested_at = datetime_format(fir.requested_datetime, "%d-%b-%Y %H:%M")
            section_label = f"Further Information Request, {requested_at}"

            owner_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Respond",
                    url=reverse("case:respond-fir", kwargs=kwargs),
                    section_label=section_label,
                ),
            )

        # add each action as a section (each section label is unique)
        for action in owner_actions:
            information = action.section_label  # type:ignore[assignment]
            r.sections.append(WorkbasketSection(information=information, actions=[action]))

    return r


def _get_approval_wb_row(
    app: ImporterApprovalRequest | ExporterApprovalRequest, user: User, is_ilb_admin: bool
) -> WorkbasketRow:
    r = WorkbasketRow()
    r.id = app.id

    r.reference = app.access_request.reference

    r.subject = ProcessTypes(app.process_type).label

    acc_req: AccessRequest = app.access_request

    r.company = "\n".join(
        [
            f"{acc_req.submitted_by} {acc_req.submitted_by.email}",
            acc_req.organisation_name,
            acc_req.organisation_address,
        ]
    )

    r.status = app.get_status_display()

    r.timestamp = app.request_date or app.created

    information = "Approval Request"

    actions: list[WorkbasketAction] = []

    if app.process_type == ProcessTypes.ExpApprovalReq:
        entity = "exporter"
        access_request_pk = acc_req.exporteraccessrequest.pk

    elif app.process_type == ProcessTypes.ImpApprovalReq:
        entity = "importer"
        access_request_pk = acc_req.importeraccessrequest.pk

    else:
        raise NotImplementedError(f"process_type: {app.process_type} not supported")

    if not app.requested_from:
        actions.append(
            WorkbasketAction(
                is_post=True,
                url=reverse(
                    "access:case-approval-take-ownership",
                    kwargs={"approval_request_pk": app.pk, "entity": entity},
                ),
                name="Take Ownership",
            )
        )

    #
    # Only show manage link if the supplied user is the request_from user.
    #
    elif app.requested_from == user:
        kwargs = {
            "access_request_pk": access_request_pk,
            "entity": entity,
            "approval_request_pk": app.pk,
        }

        actions.append(
            WorkbasketAction(
                is_post=False,
                url=reverse("access:case-approval-respond", kwargs=kwargs),
                name="Manage",
            )
        )

    r.sections.append(WorkbasketSection(information=information, actions=actions))

    return r


def get_mailshot_row(mailshot: Mailshot, user: User, is_ilb_admin: bool) -> WorkbasketRow:
    mailshot_sections = [
        WorkbasketSection(
            "Mailshot Received",
            actions=[
                WorkbasketAction(
                    is_post=False,
                    url=reverse("mailshot-detail-received", kwargs={"mailshot_pk": mailshot.id}),
                    name="View",
                ),
                WorkbasketAction(
                    is_post=True,
                    url=reverse("mailshot-clear", kwargs={"mailshot_pk": mailshot.id}),
                    name="Clear",
                ),
            ],
        )
    ]

    r = WorkbasketRow(
        id=mailshot.id,
        reference=mailshot.get_reference(),
        subject="\n".join(["Mailshot", mailshot.title]),
        company="N/a",
        company_agent="",
        status=mailshot.get_status_display(),
        timestamp=mailshot.published_datetime,
        sections=mailshot_sections,
    )

    return r
