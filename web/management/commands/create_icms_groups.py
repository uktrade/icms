from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from web.permissions import Perms


class Command(BaseCommand):
    help = """Create ICMS Groups."""

    def handle(self, *args, **options):
        create_groups()


def create_groups():
    for group_name, permission_codenames in get_groups().items():
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
            Perms.sys.mailshot_access,
        ],
        "Importer User": [
            #
            # Page permissions
            Perms.page.view_importer_details.codename,
            #
            # Sys permissions
            Perms.sys.importer_access.codename,
        ],
        "Exporter User": [
            #
            # Page permissions
            Perms.page.view_exporter_details.codename,
            #
            # Sys permissions
            Perms.sys.exporter_access.codename,
        ],
    }
