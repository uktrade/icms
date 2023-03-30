from .perms import (
    ExporterObjectPermissions,
    ImporterObjectPermissions,
    PagePermissions,
    Perms,
    SysPerms,
)
from .service import (
    can_user_edit_firearm_authorities,
    can_user_edit_org,
    can_user_edit_section5_authorities,
    can_user_manage_org_contacts,
    can_user_view_org,
    get_user_exporter_permissions,
    get_user_importer_permissions,
    organisation_add_contact,
    organisation_get_contacts,
    organisation_remove_contact,
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
    "can_user_manage_org_contacts",
    "can_user_edit_firearm_authorities",
    "can_user_edit_org",
    "can_user_edit_section5_authorities",
    "can_user_view_org",
    "get_user_exporter_permissions",
    "get_user_importer_permissions",
    "organisation_add_contact",
    "organisation_get_contacts",
    "organisation_remove_contact",
    "PermissionTextChoice",
    "importer_object_permissions",
    "exporter_object_permissions",
    "all_permissions",
]
