import oracledb
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from web.models import User

from .config.post_migrate import GROUPS_TO_ROLES
from .utils.db import CONNECTION_CONFIG


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.apply_user_permissions()

    def apply_user_permissions(self):
        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            self.fetch_data(connection, "ILB Case Officer")
            self.fetch_data(connection, "Home Office Case Officer")
            self.fetch_data(connection, "NCA Case Officer")

    def fetch_data(self, connection: oracledb.Connection, group_name: str):
        self.stdout.write(f"Adding users to {group_name} group")
        query = GROUPS_TO_ROLES[group_name]
        group = Group.objects.get(name=group_name)

        with connection.cursor() as cursor:
            cursor.execute(query)

            while True:
                rows = cursor.fetchmany(1000)

                if not rows:
                    break

                self.assign_user_groups(group, rows)

    def assign_user_groups(self, group: Group, rows: list[tuple[str, str]]):
        for row in rows:
            user = User.objects.get(username=row[0])
            user.groups.add(group)
