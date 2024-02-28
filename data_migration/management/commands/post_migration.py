import argparse

import oracledb
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import ArrayField
from django.core.management.base import BaseCommand
from django.db.models import F, TextField, Value
from django.db.models.expressions import Func
from guardian.shortcuts import remove_perm

from web.models import Constabulary, Exporter, Importer, UniqueReference, User
from web.permissions import (
    constabulary_add_contact,
    get_org_obj_permissions,
    organisation_add_contact,
)

from .config.post_migrate import GROUPS_TO_ROLES, MODEL_REFERENCES
from .types import Ref
from .utils.db import CONNECTION_CONFIG


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--skip_ref",
            help="Skip creating references",
            action="store_true",
        )
        parser.add_argument(
            "--skip_perms",
            help="Skip creating permissions",
            action="store_true",
        )

    def handle(self, *args, **options) -> None:
        skip_refs = options["skip_ref"]
        skip_perms = options["skip_perms"]

        if not skip_refs:
            self.stdout.write("Running create_unique_references...")
            self.create_unique_references("import")
            self.create_unique_references("export")
            self.create_unique_references("mailshot")
            self.create_unique_references("access")

        if not skip_perms:
            self.apply_user_permissions()

    def create_unique_references(self, ref_type: Ref) -> None:
        """Create UniqueReference objects from ImportApplication.reference, ExportApplication.reference

        'IMA/2010/00001' -> ['IMA', '2010', '00001'] -> UniqueReference(prefix='IMA', year=2010, reference=1)
        """
        self.stdout.write(f"Creating {ref_type} references")

        formatted_reference = Func(
            F("reference"),
            Value("/"),
            function="regexp_split_to_array",
            output=ArrayField(TextField()),
        )

        model_reference = MODEL_REFERENCES[ref_type]
        model = model_reference.model
        filter_params = model_reference.filter_params
        year = model_reference.year

        references = (
            model.objects.filter(**filter_params)
            .annotate(formatted_reference=formatted_reference)
            .values_list("formatted_reference", flat=True)
        )

        UniqueReference.objects.bulk_create(
            [
                (
                    UniqueReference(prefix=ref[0], year=int(ref[1]), reference=int(ref[2]))
                    if year
                    else UniqueReference(prefix=ref[0], reference=int(ref[1]))
                )
                for ref in references
            ],
            batch_size=2000,
        )

    def apply_user_permissions(self) -> None:
        """Fetch user teams and roles from V1 and apply groups and object permissions in V2"""

        self.stdout.write("Running apply_user_permissions...")

        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            self.fetch_permission_data(connection, "ILB Case Officer")
            self.fetch_permission_data(connection, "Home Office Case Officer")
            self.fetch_permission_data(connection, "NCA Case Officer")
            self.fetch_permission_data(connection, "Import Search User")
            self.fetch_permission_data(connection, "Importer User")
            self.fetch_permission_data(connection, "Exporter User")

            # TODO ICMSLST-2128: Constabulary contact permissions may not be migrated to V2
            self.fetch_permission_data(connection, "Constabulary Contact")

    def fetch_permission_data(self, connection: oracledb.Connection, group_name: str) -> None:
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
                    self.assign_org_permissions(group_name, rows)
                elif group_name == "Constabulary Contact":
                    self.assign_constabulary_contacts(rows)
                else:
                    self.assign_user_groups(group_name, rows)

    def assign_constabulary_contacts(self, rows: list[tuple[str, str, int]]):
        """Assign contabulary contact permissions to the usernames provided in the data

        :param rows: each row of data should contain (username, roles, object_id)
        """
        for username, _, constabulary_id in rows:
            constabulary = Constabulary.objects.get(pk=constabulary_id)
            user = User.objects.get(username=username)
            constabulary_add_contact(constabulary, user)

    def assign_org_permissions(self, group_name: str, rows: list[tuple[str, str, int]]) -> None:
        """Assign org permissions to the usernames provided in the data

        :param group_name: the name of the group used to determine the org type to apply the permissions to
        :param rows: each row of data should contain (username, roles, object_id)
        """
        for username, roles, org_id in rows:
            user = User.objects.get(username=username)

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
        group = Group.objects.get(name=group_name)

        for username, _ in rows:
            user = User.objects.get(username=username)
            user.groups.add(group)
