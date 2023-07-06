import oracledb
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from guardian.shortcuts import remove_perm

from web.models import Exporter, Importer, User
from web.permissions import get_org_obj_permissions, organisation_add_contact

from .config.post_migrate import GROUPS_TO_ROLES
from .utils.db import CONNECTION_CONFIG


class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        self.apply_user_permissions()

    def apply_user_permissions(self) -> None:
        """Fetch user teams and roles from V1 and apply groups and object permissions in V2"""
        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            self.fetch_data(connection, "ILB Case Officer")
            self.fetch_data(connection, "Home Office Case Officer")
            self.fetch_data(connection, "NCA Case Officer")
            self.fetch_data(connection, "Importer User")
            self.fetch_data(connection, "Exporter User")

    def fetch_data(self, connection: oracledb.Connection, group_name: str) -> None:
        """Fetch user teams and roles from V1 and call methods to assign groups and permissions
        to the returned users"""

        self.stdout.write(f"Adding users to {group_name} group")
        query = GROUPS_TO_ROLES[group_name]

        with connection.cursor() as cursor:
            cursor.execute(query)

            while True:
                rows = cursor.fetchmany(1000)

                if not rows:
                    break

                if group_name in ("Importer User", "Exporter User"):
                    self.assign_object_permissions(group_name, rows)
                else:
                    self.assign_user_groups(group_name, rows)

    def assign_object_permissions(self, group_name: str, rows: list[tuple[str, str, int]]) -> None:
        """Assign object permissions to the usernames provided in the data

        :param group_name: the name of the group used to determine the object type to apply the permissions to
        :param rows: each row of data should contain (username, roles, object_id)
        """
        for row in rows:
            user = User.objects.get(username=row[0])
            roles = row[1]
            org_id = row[2]

            if group_name == "Importer User":
                org = Importer.objects.get(pk=org_id)
            else:
                org = Exporter.objects.get(pk=org_id)

            assign_manage = ":AGENT_APPROVER" in roles

            organisation_add_contact(org, user, assign_manage)

            # Check user should have view permissions
            if ":VIEW" not in roles:
                obj_perms = get_org_obj_permissions(org)
                remove_perm(obj_perms.view, user, org)

            # Check user should have edit permissions
            if ":EDIT_APP" not in roles and ":VARY_APP" not in roles:
                obj_perms = get_org_obj_permissions(org)
                remove_perm(obj_perms.edit, user, org)

    def assign_user_groups(self, group_name: str, rows: list[tuple[str, str]]) -> None:
        """Assign groups to the usernames provided in the data

        :param group_name: the name of the group to be added to the user
        :param rows: each row of data should contain (username, roles)
        """
        for row in rows:
            user = User.objects.get(username=row[0])
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
