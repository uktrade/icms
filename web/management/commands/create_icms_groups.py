from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from web.permissions import Perms


class Command(BaseCommand):
    help = """Create ICMS Groups."""

    def handle(self, *args, **options):
        create_groups()


def create_groups():
    for group_name, permission_codenames in get_groups().items():
        if [p for p in permission_codenames if "web." in p]:
            raise ValueError("Each permission should use .codename property")

        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(codename__in=permission_codenames)

        group.permissions.set(permissions)
        group.save()


def get_groups():
    return {
        "ILB Case Officer": [
            #
            # Page permissions
            Perms.page.view_permission_harness.codename,
            Perms.page.view_importer_details.codename,
            Perms.page.view_exporter_details.codename,
            #
            # Sys permissions
            Perms.sys.ilb_admin.codename,
            Perms.sys.edit_firearm_authorities.codename,
            Perms.sys.edit_section_5_firearm_authorities.codename,
            Perms.sys.mailshot_access.codename,
            Perms.sys.search_all_cases.codename,
        ],
        Perms.obj.importer.get_group_name(): [
            #
            # Page permissions
            Perms.page.view_importer_details.codename,
            #
            # Sys permissions
            Perms.sys.importer_access.codename,
        ],
        Perms.obj.exporter.get_group_name(): [
            #
            # Page permissions
            Perms.page.view_exporter_details.codename,
            #
            # Sys permissions
            Perms.sys.exporter_access.codename,
        ],
    }
