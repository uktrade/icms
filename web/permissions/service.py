import dataclasses
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeAlias

from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import QuerySet, Value
from guardian.shortcuts import assign_perm, get_objects_for_user, get_user_perms
from guardian.shortcuts import get_users_with_perms as get_users_with_obj_perm
from guardian.shortcuts import remove_perm

from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes
from web.models import (
    Constabulary,
    Exporter,
    ExporterUserObjectPermission,
    Importer,
    ImporterUserObjectPermission,
    User,
)
from web.permissions import (
    ExporterObjectPermissions,
    ImporterObjectPermissions,
    PagePermissions,
    Perms,
    SysPerms,
)
from web.reports.constants import ReportType

if TYPE_CHECKING:
    from web.models import Report

ORGANISATION: TypeAlias = Importer | Exporter
IMP_OR_EXP_PERMS_T = type[ImporterObjectPermissions | ExporterObjectPermissions]


@dataclasses.dataclass
class AppChecker:
    """Class used to check permissions relating to an application."""

    user: User
    app: ImpOrExp

    # Some system permissions to cache when initializing class
    is_ilb_admin: bool = dataclasses.field(init=False)
    has_org_access: bool = dataclasses.field(init=False)

    # Org attributes to use when checking permissions
    org: ORGANISATION = dataclasses.field(init=False)
    agent_org: ORGANISATION = dataclasses.field(init=False)
    obj_perms: IMP_OR_EXP_PERMS_T = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.is_ilb_admin = self.user.has_perm(Perms.sys.ilb_admin)

        if self.app.is_import_application():
            self.has_org_access = self.user.has_perm(Perms.sys.importer_access)
            self.org = self.app.importer
        else:
            self.has_org_access = self.user.has_perm(Perms.sys.exporter_access)
            self.org = self.app.exporter

        self.agent_org = self.app.agent

        # Org and agent_org will be the same model type so pass in one of them.
        self.obj_perms = get_org_obj_permissions(self.org)

    def can_edit(self):
        """Check if the user can edit an application for the linked organisation.

        If an agent organisation is defined the user *must* be able to edit the agent.
        """

        if self.agent_org:
            org_to_check = self.agent_org
        else:
            org_to_check = self.org

        can_edit_org_apps = self.user.has_perm(self.obj_perms.edit, org_to_check)

        return self.has_org_access and can_edit_org_apps

    def can_view(self):
        """Check if the user can view an application.

        They need to be able to view the main organisation applications or the
        agent organisation applications if defined.

        ILB_ADMIN's can always view an application.
        Users who can view all cases can always view an application (e.g. NCA Case Officers)
        """

        if self.is_ilb_admin:
            return True

        is_import_app = self.app.is_import_application()

        # Logic for users who can search all import applications e.g. NCA Case Officers
        if is_import_app and self.user.has_perm(Perms.sys.search_import_cases):
            return True

        # Logic for users who can search all export applications e.g. Export Search User
        if not is_import_app and self.user.has_perm(Perms.sys.search_export_cases):
            return True

        if not self.has_org_access:
            return False

        return self.user.has_perm(self.obj_perms.view, self.org) or (
            self.agent_org and self.user.has_perm(self.obj_perms.view, self.agent_org)
        )

    def can_vary(self):
        """Check if the user can vary an application for the linked organisation.

        They need to be able to edit the main organisation applications or the
        agent organisation applications if defined.

        ILB_ADMIN's can always vary an application.
        """

        if self.is_ilb_admin:
            return True

        if not self.has_org_access:
            return False

        return self.user.has_perm(self.obj_perms.edit, self.org) or (
            self.agent_org and self.user.has_perm(self.obj_perms.edit, self.agent_org)
        )


class UserOrgPerms(NamedTuple):
    user_id: int
    content_object_id: int
    org_permissions: list[str]


def get_user_importer_permissions(
    user: User, importer: Importer | None = None
) -> list[UserOrgPerms]:
    filter_kwargs = {"user": user}

    if importer:
        filter_kwargs["content_object"] = importer

    iuo_perms = (
        ImporterUserObjectPermission.objects
        # Group by
        .values("user_id", "content_object_id")
        .filter(**filter_kwargs)
        # Field annotations
        .annotate(org_permissions=ArrayAgg("permission__codename", default=Value([])))
        .order_by("user_id", "content_object_id")
        .values_list("user_id", "content_object_id", "org_permissions", named=True)
    )

    return iuo_perms


def get_user_exporter_permissions(
    user: User, exporter: Exporter | None = None
) -> list[UserOrgPerms]:
    filter_kwargs = {"user": user}

    if exporter:
        filter_kwargs["content_object"] = exporter

    euo_perms = (
        ExporterUserObjectPermission.objects
        # Group by
        .values("user_id", "content_object_id")
        .filter(**filter_kwargs)
        # Field annotations
        .annotate(org_permissions=ArrayAgg("permission__codename", default=Value([])))
        .order_by("user_id", "content_object_id")
        .values_list("user_id", "content_object_id", "org_permissions", named=True)
    )

    return euo_perms


def organisation_get_contacts(
    org: ORGANISATION, *, perms: list[str] | None = None
) -> QuerySet[User]:
    """Current active contacts associated with importer, importer agent or exporter.

    An importer agent is still simply an importer.
    """

    if not perms:
        obj_perms = get_org_obj_permissions(org)

        # Remove the agent permission from both org permission lists.
        perms = [p.codename for p in obj_perms if p != obj_perms.is_agent]

    org_contacts: QuerySet[User] = get_users_with_obj_perm(org, only_with_perms_in=perms)

    # Ensure they have org access
    org_contacts = filter_users_with_org_access(org, org_contacts)

    return org_contacts.filter(is_active=True)


def organisation_add_contact(org: ORGANISATION, user: User, assign_manage: bool = False) -> None:
    """Add a user to an organisation.

    :param org: Organisation instance
    :param user: User instance
    :param assign_manage: Assigns the manage_contacts_and_agents object permission if True.
    """

    obj_perms = get_org_obj_permissions(org)

    if assign_manage:
        if org.is_agent():
            # Agent organisation contacts never have the manage permission set.
            raise ValueError(f"Unable to assign manage perm to agent org: {org.name}")

        assign_perm(obj_perms.manage_contacts_and_agents, user, org)

    for perm in [obj_perms.view, obj_perms.edit]:
        assign_perm(perm, user, org)

    if org.is_agent():
        assign_perm(obj_perms.is_agent, user, org.get_main_org())

    add_group(user, obj_perms.get_group_name())


def organisation_remove_contact(org: ORGANISATION, user: User) -> None:
    """Remove a user from an organisation."""

    for perm in get_user_perms(user, org):
        remove_perm(perm, user, org)

    obj_perms = get_org_obj_permissions(org)

    if org.is_agent():
        remove_perm(obj_perms.is_agent, user, org.get_main_org())

    # Is the user linked to any other orgs
    other_orgs = get_objects_for_user(user, obj_perms.values, any_perm=True)

    if not other_orgs.exists():
        remove_group(user, obj_perms.get_group_name())


def can_user_view_org(user: User, org: ORGANISATION) -> bool:
    """Check if the supplied user can view an organisation."""

    obj_perms = get_org_obj_permissions(org)

    can_view_org = (
        user.has_perm(obj_perms.view, org)
        or user.has_perm(obj_perms.edit, org)
        or user.has_perm(obj_perms.manage_contacts_and_agents, org)
    )

    if org.is_agent():
        main_org = org.get_main_org()
        can_view_main_org = (
            user.has_perm(obj_perms.view, main_org)
            or user.has_perm(obj_perms.edit, main_org)
            or user.has_perm(obj_perms.manage_contacts_and_agents, main_org)
        )
    else:
        can_view_main_org = False

    is_admin = is_user_org_admin(user, org)

    return is_admin or can_view_org or can_view_main_org


def can_user_edit_org(user: User, org: ORGANISATION) -> bool:
    """Check if the supplied user can edit an organisation."""

    obj_perms = get_org_obj_permissions(org)

    # Can the user edit / manage contacts of the org directly
    can_edit_org = user.has_perm(obj_perms.edit, org) or user.has_perm(
        obj_perms.manage_contacts_and_agents, org
    )

    # Can the user edit / manage contacts of the parent org
    if org.is_agent():
        main_org = org.get_main_org()
        can_edit_main_org = user.has_perm(obj_perms.edit, main_org) or user.has_perm(
            obj_perms.manage_contacts_and_agents, main_org
        )
    else:
        can_edit_main_org = False

    is_admin = is_user_org_admin(user, org)

    return is_admin or can_edit_org or can_edit_main_org


def can_user_manage_org_contacts(user: User, org: ORGANISATION) -> bool:
    """Check if the supplied user can manage organisation contacts."""

    obj_perms = get_org_obj_permissions(org)

    # Can the user manage contacts of the org directly
    can_manage_contacts = user.has_perm(obj_perms.manage_contacts_and_agents, org)

    # Can the user manage contacts of the parent org
    if org.is_agent():
        can_manage_main_org_contacts = user.has_perm(
            obj_perms.manage_contacts_and_agents, org.get_main_org()
        )
    else:
        can_manage_main_org_contacts = False

    is_admin = is_user_org_admin(user, org)

    return is_admin or can_manage_contacts or can_manage_main_org_contacts


def is_user_org_admin(user: User, org: ORGANISATION) -> bool:
    """Return True if the supplied user is an org admin.

    An org admin is a user who can edit that type of organisation.
    """

    match org:
        case Importer():
            return user.has_perm(Perms.sys.importer_admin)
        case Exporter():
            return user.has_perm(Perms.sys.exporter_admin)
        case _:
            raise ValueError(f"Unknown org {org}")


def is_user_agent_of_org(user: User, org: ORGANISATION) -> bool:
    """Return True if the user is an agent of the supplied organisation."""
    obj_perms = get_org_obj_permissions(org)

    return user.has_perm(obj_perms.is_agent, org)


def constabulary_get_contacts(
    constabulary: Constabulary, *, perms: list[str] | None = None
) -> QuerySet[User]:
    if not perms:
        perms = [p.codename for p in Perms.obj.constabulary]

    org_contacts: QuerySet[User] = get_users_with_obj_perm(constabulary, only_with_perms_in=perms)

    return org_contacts.filter(is_active=True)


def constabulary_add_contact(constabulary: Constabulary, user: User) -> None:
    for perm in Perms.obj.constabulary.values:
        assign_perm(perm, user, constabulary)

    add_group(user, Perms.obj.constabulary.get_group_name())


def constabulary_remove_contact(constabulary: Constabulary, user: User) -> None:
    for perm in get_user_perms(user, constabulary):
        remove_perm(perm, user, constabulary)

    # Is the user linked to any other constabularies
    other_orgs = get_objects_for_user(user, Perms.obj.constabulary.values, any_perm=True)

    if not other_orgs.exists():
        remove_group(user, Perms.obj.constabulary.get_group_name())


def can_user_edit_firearm_authorities(user: User) -> bool:
    return user.has_perm(Perms.sys.edit_firearm_authorities)


def can_user_edit_section5_authorities(user: User) -> bool:
    return user.has_perm(Perms.sys.edit_section_5_firearm_authorities)


def can_user_view_search_cases(user: User, case_type: Literal["import", "export"]) -> bool:
    match case_type:
        case "import":
            return user.has_perm(Perms.page.view_import_case_search)
        case "export":
            return user.has_perm(Perms.page.view_export_case_search)
        case _:
            return False


def get_users_with_permission(
    permission: str | Permission, include_superusers: bool = False
) -> QuerySet[User]:
    """Returns users that have the given permission.

    Returns an empty queryset if no users who have the perm found.

    Supported permission formats:
    - "<app label>.<permission codename>" format
    - Permission instance.

    See django Docs:
    https://docs.djangoproject.com/en/4.2/ref/contrib/auth/#django.contrib.auth.models.UserManager.with_perm
    """

    return User.objects.with_perm(
        permission,
        include_superusers=include_superusers,
        backend="web.auth.backends.ModelAndObjectPermissionBackend",
    )


def get_all_case_officers() -> QuerySet[User]:
    """Returns users who are case officers."""

    return get_users_with_permission(Perms.sys.ilb_admin)


def get_ilb_case_officers() -> QuerySet[User]:
    """Returns users who are ilb case officers."""

    return get_all_case_officers().exclude(pk__in=get_sanctions_case_officers().values("pk"))


def get_sanctions_case_officers() -> QuerySet[User]:
    """Returns users who are sanctions case officers."""

    return get_users_with_permission(Perms.sys.sanctions_case_officer)


def get_case_officers_for_process_type(process_type: ProcessTypes) -> QuerySet[User]:
    """Returns the case officers for a given process type."""

    match process_type:
        case ProcessTypes.SANCTIONS:
            return get_all_case_officers()
        case _:
            return get_ilb_case_officers()


def get_org_obj_permissions(org: ORGANISATION) -> IMP_OR_EXP_PERMS_T:
    match org:
        case Importer():
            return ImporterObjectPermissions
        case Exporter():
            return ExporterObjectPermissions
        case _:
            raise ValueError(f"Unknown org {org}")


def add_group(user: User, group_name: str) -> None:
    group = Group.objects.get(name=group_name)
    user.groups.add(group)


def remove_group(user: User, group_name: str) -> None:
    group = Group.objects.get(name=group_name)
    user.groups.remove(group)


def filter_users_with_org_access(org: ORGANISATION, users: QuerySet[User]) -> QuerySet[User]:
    match org:
        case Importer():
            org_access = Perms.sys.importer_access.codename
        case Exporter():
            org_access = Perms.sys.exporter_access.codename
        case _:
            raise ValueError(f"Unknown org {org}")

    # Note: We are ignoring user permissions by design
    return users.filter(groups__permissions__codename=org_access).distinct()


def get_report_permission(report: "Report") -> PagePermissions:
    match report.report_type:
        case ReportType.ISSUED_CERTIFICATES:
            return Perms.page.view_report_issued_certificates
        case ReportType.IMPORT_LICENCES:
            return Perms.page.view_report_import_licences
        case ReportType.ACCESS_REQUESTS:
            return Perms.page.view_report_access_requests
        case ReportType.SUPPLEMENTARY_FIREARMS:
            return Perms.page.view_report_supplementary_firearms
        case ReportType.FIREARMS_LICENCES:
            return Perms.page.view_report_firearms_licences
        case ReportType.ACTIVE_USERS:
            return Perms.page.view_report_active_users
        case _:
            raise ValueError(f"Unknown Report Type {report.report_type}")


def can_user_view_report(user: User, report: "Report") -> bool:
    permission = get_report_permission(report)
    return user.has_perm(permission)


def get_report_type_for_permission(perm: PagePermissions | SysPerms) -> ReportType | None:
    match perm:
        case PagePermissions.view_report_issued_certificates:
            return ReportType.ISSUED_CERTIFICATES
        case PagePermissions.view_report_firearms_licences:
            return ReportType.FIREARMS_LICENCES
        case PagePermissions.view_report_supplementary_firearms:
            return ReportType.SUPPLEMENTARY_FIREARMS
        case PagePermissions.view_report_access_requests:
            return ReportType.ACCESS_REQUESTS
        case PagePermissions.view_report_import_licences:
            return ReportType.IMPORT_LICENCES
        case PagePermissions.view_report_active_users:
            return ReportType.ACTIVE_USERS
        case _:
            return None
