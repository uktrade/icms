import dataclasses
from collections import defaultdict
from typing import Any, Literal

from django.db import models
from django.db.models.functions import Coalesce

from web.models import ExportApplication, ImportApplication, User
from web.permissions import (
    ExporterObjectPermissions,
    ImporterObjectPermissions,
    Perms,
    get_user_exporter_permissions,
    get_user_importer_permissions,
)


def get_order_by_datetime(case_type: str) -> Any:
    if case_type == "import":
        return models.F("submit_datetime")
    else:
        return Coalesce("submit_datetime", "created")


def get_user_import_applications(user: User) -> models.QuerySet[ImportApplication]:
    """Returns Import Applications the user has access to."""

    if user.has_perm(Perms.sys.search_all_cases):
        return ImportApplication.objects.all()

    perms_to_check = [
        Perms.obj.importer.view.codename,
        Perms.obj.importer.edit.codename,
        Perms.obj.importer.manage_contacts_and_agents.codename,
    ]

    applications = ImportApplication.objects.annotate(
        main_contact=models.FilteredRelation(
            "importer__importeruserobjectpermission",
            condition=models.Q(importer__importeruserobjectpermission__user=user),
        ),
        agent_contact=models.FilteredRelation(
            "agent__importeruserobjectpermission",
            condition=models.Q(agent__importeruserobjectpermission__user=user),
        ),
    )

    applications = applications.filter(
        models.Q(main_contact__permission__codename__in=perms_to_check)
        | models.Q(agent_contact__permission__codename__in=perms_to_check)
    )

    # One importer to many permissions so filter on distinct applications
    applications = applications.distinct("pk")

    return applications


def get_user_export_applications(user: User) -> models.QuerySet[ExportApplication]:
    """Returns Export Applications the user has access to."""

    if user.has_perm(Perms.sys.search_all_cases):
        return ExportApplication.objects.all()

    perms_to_check = [
        Perms.obj.exporter.view.codename,
        Perms.obj.exporter.edit.codename,
        Perms.obj.exporter.manage_contacts_and_agents.codename,
    ]

    applications = ExportApplication.objects.annotate(
        main_contact=models.FilteredRelation(
            "exporter__exporteruserobjectpermission",
            condition=models.Q(exporter__exporteruserobjectpermission__user=user),
        ),
        agent_contact=models.FilteredRelation(
            "agent__exporteruserobjectpermission",
            condition=models.Q(agent__exporteruserobjectpermission__user=user),
        ),
    )

    applications = applications.filter(
        models.Q(main_contact__permission__codename__in=perms_to_check)
        | models.Q(agent_contact__permission__codename__in=perms_to_check)
    )

    # One exporter to many permissions so filter on distinct applications
    applications = applications.distinct("pk")

    return applications


@dataclasses.dataclass
class UserOrganisationPermissions:
    user: User
    case_type: Literal["import", "export"]

    # key: org primary key, value: set of permissions
    _cache: dict[int, set[str]] = dataclasses.field(init=False)
    has_ilb_admin_perm: bool = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.has_ilb_admin_perm = self.user.has_perm(Perms.sys.ilb_admin)

        if self.case_type == "import":
            user_org_permissions = get_user_importer_permissions(self.user)
        else:
            user_org_permissions = get_user_exporter_permissions(self.user)

        self._cache = defaultdict(set)

        for uop in user_org_permissions:
            self._cache[uop.content_object_id] = set(uop.org_permissions)

    def has_permission(
        self,
        organisation_pk: int,
        *permissions: ImporterObjectPermissions | ExporterObjectPermissions,
        any_perm: bool = False,
        include_ilb_admin: bool = True,
    ) -> bool:
        """Check if the initialised user has permissions for a given organisation.

        :param organisation_pk: Primary key of organisation to check.
        :param permissions: Single permission, or sequence of permissions to check.
        :param any_perm: If True, any of permission in sequence is accepted. Default is False.
        :param include_ilb_admin: If True, return True if user has ilb_admin permission.
        """

        user_org_perms = self._cache[organisation_pk]

        required_perms = {p.codename for p in permissions}

        if any_perm:
            # True if any required perms are in the user org perms
            has_permission = bool(user_org_perms.intersection(required_perms))
        else:
            # True if all required perms are in the user org perms
            has_permission = user_org_perms.issuperset(required_perms)

        return (include_ilb_admin and self.has_ilb_admin_perm) or has_permission
