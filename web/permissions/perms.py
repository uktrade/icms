from .types import PermissionTextChoice


class PagePermissions(PermissionTextChoice):
    view_permission_harness = (
        "web.can_view_permission_harness",
        "Can view the permission test harness",
    )
    view_importer_details = (
        "web.can_view_importer_details",
        "Can view the importer details list page.",
    )
    view_exporter_details = (
        "web.can_view_exporter_details",
        "Can view the exporter details list page.",
    )
    view_import_case_search = (
        "web.can_view_import_case_search",
        "Can view search import applications page",
    )
    view_export_case_search = (
        "web.can_view_export_case_search",
        "Can view search certificate applications page",
    )


class SysPerms(PermissionTextChoice):
    importer_access = "web.importer_access", "Can act as an importer"
    exporter_access = "web.exporter_access", "Can act as an exporter"
    ilb_admin = "web.ilb_admin", "Is an ILB administrator"
    edit_firearm_authorities = (
        "web.edit_firearm_authorities",
        "Can edit Importer Verified Firearms Authorities",
    )
    edit_section_5_firearm_authorities = (
        "web.edit_section_5_firearm_authorities",
        "Can edit Importer Verified Section 5 Firearm Authorities",
    )
    search_all_cases = ("web.search_all_cases", "Can search across all cases.")

    # This permission isn't used anywhere.
    mailshot_access = "web.mailshot_access", "Can maintain mailshots"


class ImporterObjectPermissions(PermissionTextChoice):
    view = ("web.view_importer", "Can view all applications and licences for a particular importer")
    edit = (
        "web.edit_importer",
        "Can create and edit new applications and vary existing licences for a particular importer",
    )
    manage_contacts_and_agents = (
        "web.manage_importer_contacts_and_agents",
        "Can approve and reject access for agents and new importer contacts",
    )
    is_contact = ("web.is_contact_of_importer", "Is contact of this importer")
    # NOTE: this is given on the "main importer" object, not on the "agent" object
    is_agent = ("web.is_agent_of_importer", "Is agent of this importer")

    @staticmethod
    def get_group_name():
        return "Importer User"


class ExporterObjectPermissions(PermissionTextChoice):
    view = (
        "web.view_exporter",
        "Can view all applications and certificates for a particular exporter",
    )
    edit = (
        "web.edit_exporter",
        "Can create and edit new applications and vary existing licences for a particular exporter",
    )
    manage_contacts_and_agents = (
        "web.manage_exporter_contacts_and_agents",
        "Can approve and reject access for agents and new exporter contacts",
    )
    is_contact = ("web.is_contact_of_exporter", "Is contact of this exporter")
    # NOTE: this is given on the "main exporter" object, not on the "agent" object
    is_agent = ("web.is_agent_of_exporter", "Is agent of this exporter")

    @staticmethod
    def get_group_name():
        return "Exporter User"


class ObjectPerms:
    importer = ImporterObjectPermissions
    exporter = ExporterObjectPermissions


class Perms:
    page = PagePermissions
    sys = SysPerms
    obj = ObjectPerms

    @classmethod
    def get_all_permissions(cls) -> list[tuple[str, str]]:
        """Return all system-wide permissions defined in IMCS - Called when creating migrations."""

        return cls.page.get_permissions() + cls.sys.get_permissions()
