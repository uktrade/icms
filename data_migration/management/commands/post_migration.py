import argparse
from typing import Any

import oracledb
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import ArrayField
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import F, TextField, Value
from django.db.models.expressions import Func
from guardian.shortcuts import remove_perm

from web.domains.template.utils import add_template_data_on_submit
from web.management.commands.add_v2_reference_data import (
    add_country_translations,
    add_inactive_countries,
    add_region_to_existing_countries,
)
from web.management.commands.utils.add_email_data import (
    add_gov_notify_templates,
    add_user_management_email_templates,
    archive_database_email_templates,
    update_database_email_templates,
)
from web.models import (
    Constabulary,
    Exporter,
    ImportApplication,
    Importer,
    UniqueReference,
    User,
)
from web.permissions import (
    constabulary_add_contact,
    get_org_obj_permissions,
    organisation_add_contact,
)

from .config.post_migrate import GROUPS_TO_ROLES, MODEL_REFERENCES
from .types import Ref
from .utils.db import CONNECTION_CONFIG


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
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
        parser.add_argument(
            "--skip_add_data",
            help="Skip populating new additional models",
            action="store_true",
        )

    def add_data_to_v2_additional_models(self):
        call_command("loaddata", "overseas_regions")
        add_region_to_existing_countries(self.stdout)
        add_inactive_countries()
        add_country_translations()
        call_command("set_icms_sites")

        add_user_management_email_templates()
        update_database_email_templates()
        archive_database_email_templates()
        add_gov_notify_templates()
        self.add_submitted_app_cover_letters()

    def handle(self, *args: Any, **options: Any) -> None:
        skip_refs = options["skip_ref"]
        skip_perms = options["skip_perms"]
        skip_add_data = options["skip_add_data"]

        if not skip_refs:
            self.stdout.write("Running create_unique_references...")
            self.create_unique_references("import")
            self.create_unique_references("export")
            self.create_unique_references("mailshot")
            self.create_unique_references("access")

        if not skip_perms:
            self.apply_user_permissions()

        if not skip_add_data:
            self.add_data_to_v2_additional_models()

    def add_submitted_app_cover_letters(self) -> None:
        """Adds cover letters to import apps which have been submitted but are not yet processing"""
        for app in ImportApplication.objects.filter(status=ImportApplication.Statuses.SUBMITTED):
            if not app.cover_letter_text:
                add_template_data_on_submit(app)

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

            # Constabulary contact permissions do not need to be migrated to V2
            # Uncomment to assign constabulary contact permissions
            # self.fetch_permission_data(connection, "Constabulary Contact")

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

    def assign_constabulary_contacts(self, rows: list[tuple[str, str, int]]) -> None:
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
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise User.DoesNotExist(f"User matching {username} does not exist")

            if group_name == "Importer User":
                try:
                    org = Importer.objects.get(pk=org_id)
                except Importer.DoesNotExist:
                    raise Importer.DoesNotExist(f"Importer with pk {org_id} does not exist")
            else:
                try:
                    org = Exporter.objects.get(pk=org_id)
                except Exporter.DoesNotExist:
                    raise Exporter.DoesNotExist(f"Exporter with pk {org_id} does not exist")

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
