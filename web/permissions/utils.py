import dataclasses
from typing import TYPE_CHECKING

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Value

from web.models import ExporterUserObjectPermission, ImporterUserObjectPermission

if TYPE_CHECKING:
    from web.models import Exporter, Importer, User


@dataclasses.dataclass(frozen=True)
class UserImporterPerms:
    user: "User"
    importer: "Importer"
    importer_perms: list[str]


@dataclasses.dataclass(frozen=True)
class UserExporterPerms:
    user: "User"
    exporter: "Exporter"
    exporter_perms: list[str]


def get_user_importer_permissions(user: "User", importer: "Importer") -> UserImporterPerms:
    iuo_perms = (
        ImporterUserObjectPermission.objects
        # Group by
        .values("user_id", "content_object_id")
        .filter(user=user, content_object=importer)
        # Field annotations
        .annotate(importer_perms=ArrayAgg("permission__codename", default=Value([])))
        .order_by("user_id", "content_object_id")
        .values_list("user_id", "content_object_id", "importer_perms", named=True)
    ).first()

    # Needed as the user may not have any perms for the supplied importer
    perms = iuo_perms.importer_perms if iuo_perms else []

    return UserImporterPerms(user, importer, perms)


def get_user_exporter_permissions(user: "User", exporter: "Exporter") -> UserExporterPerms:
    euo_perms = (
        ExporterUserObjectPermission.objects
        # Group by
        .values("user_id", "content_object_id")
        .filter(user=user, content_object=exporter)
        # Field annotations
        .annotate(exporter_perms=ArrayAgg("permission__codename", default=Value([])))
        .order_by("user_id", "content_object_id")
        .values_list("user_id", "content_object_id", "exporter_perms", named=True)
    ).first()

    # Needed as the user may not have any perms for the supplied exporter
    perms = euo_perms.exporter_perms if euo_perms else []

    return UserExporterPerms(user, exporter, perms)
