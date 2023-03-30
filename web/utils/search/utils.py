from typing import Any

from django.db import models
from django.db.models.functions import Coalesce

from web.models import ExportApplication, ImportApplication, User
from web.permissions import Perms


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
        Perms.obj.importer.is_contact.codename,
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
        Perms.obj.exporter.is_contact.codename,
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
