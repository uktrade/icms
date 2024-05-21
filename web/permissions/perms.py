from .types import PermissionTextChoice


class PagePermissions(PermissionTextChoice):
    view_permission_harness = (
        "web.can_view_permission_harness",
        "Can view the permission test harness",
    )
    view_l10n_harness = (
        "web.can_view_l10n_harness",
        "Can view the L10N test harness",
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
    view_imi = ("web.view_imi", "Can view IMI pages.")
    view_documents_constabulary = (
        "web.can_view_documents_constabulary",
        "Can view issued documents within constabulary region page",
    )
    view_report_issued_certificates = (
        "web.can_view_report_issued_certificates",
        "Can view Issued Certificate Report",
    )
    view_report_access_requests = (
        "web.can_view_report_access_requests",
        "Can view Access Requests Report",
    )
    view_report_import_licences = (
        "web.can_view_report_import_licences",
        "Can view Import Licences Report",
    )
    view_report_supplementary_firearms = (
        "web.can_view_report_supplementary_firearms",
        "Can view Supplementary Firearms Report",
    )
    view_report_firearms_licences = (
        "web.can_view_report_firearms_licences",
        "Can view Firearms Licences Report",
    )
    view_report_active_users = (
        "web.can_view_report_active_users",
        "Can view Active Users Report",
    )


class SysPerms(PermissionTextChoice):
    importer_access = "web.importer_access", "Can act as an importer"
    exporter_access = "web.exporter_access", "Can act as an exporter"
    ilb_admin = "web.ilb_admin", "Is an ILB administrator"
    sanctions_case_officer = "web.sanctions_case_officer", "Is a sanctions caseworker"
    importer_regulator = "web.importer_regulator", "Is an Importer Regulator"
    importer_admin = "web.importer_admin", "Can manage Importer records."
    exporter_admin = "web.exporter_admin", "Can manage Exporter records."
    commodity_admin = "web.commodity_admin", "Is a commodity administrator"
    manage_sanction_contacts = "web.manage_sanction_contacts", "Manage sanction email contacts"
    manage_signatures = "web.manage_signatures", "Manage signatures"
    access_reports = "web.access_reports", "Access reports"

    edit_firearm_authorities = (
        "web.edit_firearm_authorities",
        "Can edit Importer Verified Firearms Authorities",
    )
    edit_section_5_firearm_authorities = (
        "web.edit_section_5_firearm_authorities",
        "Can edit Importer Verified Section 5 Firearm Authorities",
    )
    search_all_cases = ("web.search_all_cases", "Can search across all cases.")
    is_icms_data_admin = "web.is_icms_data_admin", "Can maintain data in the ICMS admin site."


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
    # NOTE: this is given on the "main exporter" object, not on the "agent" object
    is_agent = ("web.is_agent_of_exporter", "Is agent of this exporter")

    @staticmethod
    def get_group_name():
        return "Exporter User"


class ConstabularyObjectPermissions(PermissionTextChoice):
    verified_fa_authority_editor = (
        "web.verified_fa_authority_editor",
        "Can view and edit importer verified firearms authorities issued by the constabulary.",
    )

    @staticmethod
    def get_group_name():
        return "Constabulary Contact"


class ObjectPerms:
    importer = ImporterObjectPermissions
    exporter = ExporterObjectPermissions
    constabulary = ConstabularyObjectPermissions


class Perms:
    page = PagePermissions
    sys = SysPerms
    obj = ObjectPerms

    @classmethod
    def get_all_permissions(cls) -> list[tuple[str, str]]:
        """Return all system-wide permissions defined in IMCS - Called when creating migrations."""

        return cls.page.get_permissions() + cls.sys.get_permissions()
