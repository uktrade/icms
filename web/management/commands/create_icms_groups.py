from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from web.permissions import Perms, StaffUserGroups


class Command(BaseCommand):
    help = """Create ICMS Groups."""

    def handle(self, *args, **options):
        create_groups()


def create_groups():
    for group_name, perms in get_groups().items():
        permission_codenames = [p.codename for p in perms]

        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(codename__in=permission_codenames)

        group.permissions.set(permissions)
        group.save()


def get_groups():
    return {
        StaffUserGroups.ILB_CASE_OFFICER.value: [
            #
            # Page permissions
            Perms.page.view_permission_harness,
            Perms.page.view_l10n_harness,
            Perms.page.view_import_case_search,
            Perms.page.view_export_case_search,
            Perms.page.view_imi,
            Perms.page.view_report_access_requests,
            Perms.page.view_report_firearms_licences,
            Perms.page.view_report_import_licences,
            Perms.page.view_report_supplementary_firearms,
            Perms.page.view_report_issued_certificates,
            Perms.page.view_report_active_users,
            #
            # Sys permissions
            Perms.sys.ilb_admin,
            Perms.sys.exporter_admin,
            Perms.sys.importer_admin,
            Perms.sys.manage_sanction_contacts,
            Perms.sys.manage_signatures,
            Perms.sys.edit_firearm_authorities,
            Perms.sys.edit_section_5_firearm_authorities,
            Perms.sys.commodity_admin,
            Perms.sys.search_all_cases,
            Perms.sys.access_reports,
        ],
        #
        # "Importer User": (System group + object permissions to related importers)
        Perms.obj.importer.get_group_name(): [
            #
            # Page permissions
            Perms.page.view_importer_details,
            Perms.page.view_import_case_search,
            #
            # Sys permissions
            Perms.sys.importer_access,
        ],
        #
        # "Exporter User": (System group + object permissions to related exporters)
        Perms.obj.exporter.get_group_name(): [
            #
            # Page permissions
            Perms.page.view_exporter_details,
            Perms.page.view_export_case_search,
            #
            # Sys permissions
            Perms.sys.exporter_access,
        ],
        StaffUserGroups.NCA_CASE_OFFICER.value: [
            # Page permissions
            Perms.sys.importer_regulator,
            Perms.page.view_import_case_search,
            Perms.page.view_report_firearms_licences,
            Perms.page.view_report_supplementary_firearms,
            # Sys permissions
            Perms.sys.search_all_cases,
            Perms.sys.access_reports,
        ],
        StaffUserGroups.HOME_OFFICE_CASE_OFFICER.value: {
            # Page permissions
            Perms.page.view_import_case_search,
            # Sys permissions
            Perms.sys.search_all_cases,
            Perms.sys.importer_regulator,
            Perms.sys.edit_section_5_firearm_authorities,
        },
        StaffUserGroups.SANCTIONS_CASE_OFFICER.value: {
            #
            # Page permissions
            Perms.page.view_import_case_search,
            #
            # Sys permissions
            Perms.sys.ilb_admin,
            Perms.sys.sanctions_case_officer,
            Perms.sys.importer_admin,
            Perms.sys.commodity_admin,
            Perms.sys.manage_sanction_contacts,
            Perms.sys.search_all_cases,
            Perms.sys.access_reports,
            Perms.page.view_report_import_licences,
            Perms.page.view_report_firearms_licences,
        },
        #
        # "Constabulary Contact" (System group + object permissions to related constabularies)
        Perms.obj.constabulary.get_group_name(): {
            #
            # Page permissions
            Perms.page.view_documents_constabulary,
            #
            # Sys permissions
            Perms.sys.importer_regulator,
            Perms.sys.edit_firearm_authorities,
        },
        StaffUserGroups.IMPORT_SEARCH_USER.value: {
            #
            # Page permissions
            Perms.page.view_import_case_search,
            #
            # Sys permissions
            Perms.sys.search_all_cases,
        },
        "ICMS Admin Site User": {
            Perms.sys.is_icms_data_admin,
            Permission.objects.get(content_type__app_label="web", codename="change_user"),
            Permission.objects.get(content_type__app_label="web", codename="view_user"),
            Permission.objects.get(content_type__app_label="web", codename="change_emailtemplate"),
            Permission.objects.get(content_type__app_label="web", codename="view_emailtemplate"),
            Permission.objects.get(content_type__app_label="web", codename="view_email"),
        },
        "Dev Admin": {
            Perms.page.view_one_login_test_account_setup,
        },
    }
