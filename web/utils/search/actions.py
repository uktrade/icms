import datetime as dt
from typing import Protocol

from dateutil import relativedelta
from django.urls import reverse
from django.utils import timezone

from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes
from web.models import ExportApplication, ImportApplication
from web.permissions import ExporterObjectPermissions, ImporterObjectPermissions

from . import types
from .utils import UserOrganisationPermissions


def get_import_record_actions(
    app: ImportApplication, user_org_perms: UserOrganisationPermissions
) -> list[types.SearchAction]:
    """Get the available actions for the supplied import application.

    :param app: Import Application record.
    :param user_org_perms:
    :return:
    """

    actions = []

    for action in [VariationRequestAction, RevokeLicenceAction, ReopenCaseAction]:
        if action.show_action(app, user_org_perms):
            actions.append(action.get_action(app))

    return actions


def get_export_record_actions(
    app: ExportApplication, user_org_perms: UserOrganisationPermissions
) -> list[types.SearchAction]:
    actions = []

    for action in [
        CopyExportApplicationAction,
        CreateTemplateAction,
        OpenVariationAction,
        RevokeCertificateAction,
        ReopenExportCaseAction,
    ]:
        if action.show_action(app, user_org_perms):
            actions.append(action.get_action(app))

    return actions


class ActionProtocol(Protocol):
    @staticmethod
    def show_action(app: ImpOrExp, uop: UserOrganisationPermissions) -> bool: ...

    @staticmethod
    def get_action(app: ImpOrExp) -> types.SearchAction: ...


_TODAY = timezone.now().date()
_THREE_YEARS_AGO_DT = dt.datetime.combine(
    _TODAY - relativedelta.relativedelta(years=3), dt.time.min, tzinfo=dt.UTC
)


#
# Applicant action (Import)
#
class VariationRequestAction(ActionProtocol):
    @staticmethod
    def show_action(app: ImportApplication, uop: UserOrganisationPermissions) -> bool:
        can_edit_org = _can_edit_org_or_agent(app, uop)

        return (
            app.status == ImpExpStatus.COMPLETED
            and can_edit_org
            and app.latest_licence_end_date
            and app.latest_licence_end_date >= _TODAY
        )

    @staticmethod
    def get_action(app: ImportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-request-variation",
                kwargs={"application_pk": app.pk, "case_type": "import"},
            ),
            name="request-variation",
            label="Request Variation",
            icon="icon-redo2",
            is_post=False,
        )


#
# ILB Admin action (Import)
#
class RevokeLicenceAction(ActionProtocol):
    @staticmethod
    def show_action(app: ImportApplication, uop: UserOrganisationPermissions) -> bool:
        return (
            app.status == ImpExpStatus.COMPLETED
            and uop.has_ilb_admin_perm
            and app.latest_licence_end_date
            and app.latest_licence_end_date > _TODAY
        )

    @staticmethod
    def get_action(app: ImportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-revoke-case",
                kwargs={"application_pk": app.pk, "case_type": "import"},
            ),
            name="revoke-licence",
            label="Revoke Licence",
            icon="icon-undo2",
            is_post=False,
        )


#
# ILB Admin action (Import)
#
class ReopenCaseAction(ActionProtocol):
    @staticmethod
    def show_action(app: ImportApplication, uop: UserOrganisationPermissions) -> bool:
        return (
            app.status in [ImpExpStatus.STOPPED, ImpExpStatus.WITHDRAWN] and uop.has_ilb_admin_perm
        )

    @staticmethod
    def get_action(app: ImportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-reopen-case",
                kwargs={"application_pk": app.pk, "case_type": "import"},
            ),
            name="reopen-case",
            label="Reopen Case",
            icon="icon-redo2",
        )


#
# Applicant action (Export)
#
class CopyExportApplicationAction(ActionProtocol):
    @staticmethod
    def show_action(app: ExportApplication, uop: UserOrganisationPermissions) -> bool:
        can_edit_org = _can_edit_org_or_agent(app, uop)

        return (
            can_edit_org and not uop.has_ilb_admin_perm and app.status != ImpExpStatus.IN_PROGRESS
        )

    @staticmethod
    def get_action(app: ImpOrExp) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-copy-export-application",
                kwargs={"application_pk": app.pk, "case_type": "export"},
            ),
            name="copy-application",
            label="Copy Application",
            icon="icon-copy",
            is_post=False,
        )


#
# Applicant action (Export)
#
class CreateTemplateAction(ActionProtocol):
    @staticmethod
    def show_action(app: ExportApplication, uop: UserOrganisationPermissions) -> bool:
        can_edit_org = _can_edit_org_or_agent(app, uop)

        return (
            can_edit_org and not uop.has_ilb_admin_perm and app.status != ImpExpStatus.IN_PROGRESS
        )

    @staticmethod
    def get_action(app: ImpOrExp) -> types.SearchAction:
        # TODO: ICMSLST-1241 Implement action
        return types.SearchAction(
            url="#",
            name="create-template",
            label="Create Template",
            icon="icon-magic-wand",
            is_post=True,
        )


#
# ILB Admin action (Export)
#
class OpenVariationAction(ActionProtocol):
    @staticmethod
    def show_action(app: ExportApplication, uop: UserOrganisationPermissions) -> bool:
        should_show = (
            app.status == ImpExpStatus.COMPLETED
            and app.decision == app.APPROVE
            and uop.has_ilb_admin_perm
        )

        if app.process_type in [ProcessTypes.CFS, ProcessTypes.COM]:
            return should_show

        elif app.process_type == ProcessTypes.GMP:
            return should_show and app.latest_certificate_issue_datetime > _THREE_YEARS_AGO_DT

        return False

    @staticmethod
    def get_action(app: ExportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-open-variation",
                kwargs={"application_pk": app.pk, "case_type": "export"},
            ),
            name="open-variation",
            label="Open Variation",
            icon="icon-redo2",
            is_post=False,
        )


#
# ILB Admin action (Export)
#
class RevokeCertificateAction(ActionProtocol):
    @staticmethod
    def show_action(app: ExportApplication, uop: UserOrganisationPermissions) -> bool:
        should_show = (
            app.status == ImpExpStatus.COMPLETED
            and app.decision == app.APPROVE
            and uop.has_ilb_admin_perm
        )

        if app.process_type in [ProcessTypes.CFS, ProcessTypes.COM]:
            return should_show

        elif app.process_type == ProcessTypes.GMP:
            return should_show and app.latest_certificate_issue_datetime > _THREE_YEARS_AGO_DT

        return False

    @staticmethod
    def get_action(app: ExportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-revoke-case",
                kwargs={"application_pk": app.pk, "case_type": "export"},
            ),
            name="revoke-certificates",
            label="Revoke Certificates",
            icon="icon-undo2",
            is_post=False,
        )


#
# ILB Admin action (Export)
#
class ReopenExportCaseAction(ActionProtocol):
    @staticmethod
    def show_action(app: ExportApplication, uop: UserOrganisationPermissions) -> bool:
        return (
            app.status in [ImpExpStatus.STOPPED, ImpExpStatus.WITHDRAWN] and uop.has_ilb_admin_perm
        )

    @staticmethod
    def get_action(app: ExportApplication) -> types.SearchAction:
        return types.SearchAction(
            url=reverse(
                "case:search-reopen-case",
                kwargs={"application_pk": app.pk, "case_type": "export"},
            ),
            name="reopen-case",
            label="Reopen Case",
            icon="icon-redo2",
        )


def _can_edit_org_or_agent(app: ImpOrExp, uop: UserOrganisationPermissions) -> bool:
    """Return true if the uop user can edit the org / agent of the supplied application.

    Notes:
        - If agent is set the application is an agent application.
        - If the user can edit the main organisation there are a main org
          contact and should be able to edit the supplied agent application.
        - If the user can edit the agent organisation then they are an agent
          contact and should be able to edit the supplied application.
    """

    perms_type = type[ImporterObjectPermissions | ExporterObjectPermissions]

    if app.is_import_application():
        obj_perms: perms_type = ImporterObjectPermissions
        check_orgs = [app.importer_id]
    else:
        obj_perms = ExporterObjectPermissions
        check_orgs = [app.exporter_id]

    if app.agent_id:
        check_orgs.append(app.agent_id)

    can_edit_org = False
    for org_id in check_orgs:
        if uop.has_permission(org_id, obj_perms.edit):
            can_edit_org = True

            break

    return can_edit_org
