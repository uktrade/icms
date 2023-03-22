from .perms import (
    ExporterObjectPermissions,
    ImporterObjectPermissions,
    PagePermissions,
    Perms,
    SysPerms,
)
from .service import (
    add_organisation_contact,
    can_manage_org_contacts,
    get_organisation_contacts,
    get_user_exporter_permissions,
    get_user_importer_permissions,
    remove_organisation_contact,
)
from .types import PermissionTextChoice

importer_object_permissions: list[tuple[str, str]] = Perms.obj.importer.get_permissions()
exporter_object_permissions: list[tuple[str, str]] = Perms.obj.exporter.get_permissions()
all_permissions: list[tuple[str, str]] = Perms.get_all_permissions()


__all__ = [
    "ExporterObjectPermissions",
    "ImporterObjectPermissions",
    "PagePermissions",
    "Perms",
    "SysPerms",
    "add_organisation_contact",
    "can_manage_org_contacts",
    "get_organisation_contacts",
    "get_user_importer_permissions",
    "get_user_exporter_permissions",
    "remove_organisation_contact",
    "PermissionTextChoice",
    "importer_object_permissions",
    "exporter_object_permissions",
    "all_permissions",
]
