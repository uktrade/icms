from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from web.permissions import Perms


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
        "ILB Case Officer": [
            #
            # Page permissions
            Perms.page.view_permission_harness,
            Perms.page.view_import_case_search,
            Perms.page.view_export_case_search,
            Perms.page.view_imi,
            #
            # Sys permissions
            Perms.sys.ilb_admin,
            Perms.sys.exporter_admin,
            Perms.sys.importer_admin,
            Perms.sys.manage_sanction_contacts,
            Perms.sys.edit_firearm_authorities,
            Perms.sys.edit_section_5_firearm_authorities,
            Perms.sys.commodity_admin,
            Perms.sys.search_all_cases,
            Perms.sys.mailshot_access,
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
        "NCA Case Officer": [
            # Page permissions
            Perms.page.view_import_case_search,
            # Sys permissions
            Perms.sys.search_all_cases,
            # NOTE: This user in V1 will also have some kind of report access that V2 hasn't implemented.
            # e.g.
            # Perms.sys.report_access
        ],
        "Home Office Case Officer": {
            # Page permissions
            Perms.page.view_import_case_search,
            # Sys permissions
            Perms.sys.search_all_cases,
            Perms.sys.importer_regulator,
            Perms.sys.edit_section_5_firearm_authorities,
        },
        "Sanctions Case Officer": {
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
            # NOTE: This user in V1 will also have some kind of report access that V2 hasn't implemented.
            # e.g.
            # Perms.sys.report_access
        },
        #
        # "Constabulary Contact" (System group + object permissions to related constabularies)
        Perms.obj.constabulary.get_group_name(): {
            #
            # Page permissions
            Perms.sys.importer_regulator,
            #
            # Sys permissions
            Perms.sys.edit_firearm_authorities,
        },
        "Import Search User": {
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
    }
