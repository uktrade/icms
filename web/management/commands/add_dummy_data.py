import datetime
from typing import Any, Collection

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.models import ImportApplicationType


class Command(BaseCommand):
    help = """Add dummy data. For development use only."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            action="store",
            help="You must specify this to enable the command to run",
            required=True,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if settings.APP_ENV not in ("local", "dev", "staging"):
            raise CommandError(
                "Can only add dummy data in 'staging', 'dev' and 'local' environments!"
            )

        # enable disabled application types so we can test/develop them
        ImportApplicationType.objects.filter(
            type__in=[
                ImportApplicationType.Types.DEROGATION,
                ImportApplicationType.Types.IRON_STEEL,
                ImportApplicationType.Types.OPT,
                ImportApplicationType.Types.SPS,
                ImportApplicationType.Types.TEXTILES,
            ]
        ).update(is_active=True)

        # exporter
        exporter = Exporter.objects.create(
            is_active=True, name="Dummy exporter", registered_number="42"
        )

        office = Office.objects.create(
            is_active=True, postcode="SW1A 1AA", address="Buckingham Palace, London"
        )
        exporter.offices.add(office)

        office = Office.objects.create(
            is_active=True, postcode="BT12 5QB", address="209 Roden St, Belfast"
        )
        exporter.offices.add(office)

        # importer
        importer = Importer.objects.create(
            is_active=True,
            name="Dummy importer",
            registered_number="84",
            eori_number="GBSIL9001730K",
            type=Importer.ORGANISATION,
        )

        office = Office.objects.create(
            is_active=True, postcode="SW1A 2HP", address="3 Whitehall Pl, Westminster, London"
        )
        importer.offices.add(office)

        office = Office.objects.create(
            is_active=True, postcode="BT12 5QB", address="209 Roden St, Belfast"
        )
        importer.offices.add(office)

        self.stdout.write("Created dummy importer/exporter")

        # agent for importer
        agent_importer = Importer.objects.create(
            is_active=True,
            name="Dummy agent for importer",
            registered_number="842",
            type=Importer.ORGANISATION,
            main_importer=importer,
        )

        office = Office.objects.create(
            is_active=True, postcode="TW6 2LA", address="Nettleton Rd, London"
        )
        agent_importer.offices.add(office)

        # agent for exporter
        agent_exporter = Exporter.objects.create(
            is_active=True,
            name="Dummy agent exporter",
            registered_number="422",
            main_exporter=exporter,
        )

        office = Office.objects.create(
            is_active=True, postcode="EN1 3SS", address="14 Mafeking Rd, Enfield"
        )
        agent_exporter.offices.add(office)

        self.stdout.write("Created dummy agent for importer/exporter")

        self.create_user(
            username="ilb_admin",
            password=options["password"],
            first_name="Ashley",
            last_name="Smith (ilb_admin)",
            permissions=[
                "importer_access",
                "exporter_access",
                "ilb_admin",
                "mailshot_access",
            ],
            linked_importers=[importer],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="ilb_admin_2",
            password=options["password"],
            first_name="Samantha",
            last_name="Stevens (ilb_admin)",
            permissions=[
                "importer_access",
                "exporter_access",
                "ilb_admin",
                "mailshot_access",
            ],
            linked_importers=[importer],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="importer_user",
            password=options["password"],
            first_name="Dave",
            last_name="Jones (importer_user)",
            permissions=[
                "importer_access",
            ],
            linked_importers=[importer],
        )

        self.create_user(
            username="exporter_user",
            password=options["password"],
            first_name="Sally",
            last_name="Davis (exporter_user)",
            permissions=[
                "exporter_access",
            ],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="agent",
            password=options["password"],
            first_name="Cameron",
            last_name="Hasra (agent)",
            permissions=[
                "importer_access",
                "exporter_access",
            ],
            linked_importer_agents=[agent_importer],
            linked_exporter_agents=[agent_exporter],
        )

        self.create_superuser("admin", options["password"])

        self.stdout.write(
            "Created following users: 'ilb_admin', 'importer_user', 'exporter_user', 'agent'"
        )
        self.stdout.write("Created following superusers: 'admin'")

    def create_user(
        self,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        permissions: list[str],
        linked_importers: Collection[Importer] = (),
        linked_exporters: Collection[Exporter] = (),
        linked_importer_agents: Collection[Importer] = (),
        linked_exporter_agents: Collection[Exporter] = (),
    ) -> User:
        """Create normal system users"""

        user = User.objects.create_user(
            username=username,
            password=password,
            password_disposition=User.FULL,
            is_superuser=False,
            account_status=User.ACTIVE,
            is_active=True,
            email=f"{username}@email.com",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=datetime.date(2000, 1, 1),
            security_question="security_question",
            security_answer="security_answer",
        )

        for permission in permissions:
            self._assign_permission(user, permission)

        for importer in linked_importers:
            assign_perm("web.is_contact_of_importer", user, importer)

        for exporter in linked_exporters:
            assign_perm("web.is_contact_of_exporter", user, exporter)

        for agent in linked_importer_agents:
            assign_perm("web.is_contact_of_importer", user, agent)
            assign_perm("web.is_agent_of_importer", user, agent.main_importer)

        for agent in linked_exporter_agents:
            assign_perm("web.is_contact_of_exporter", user, agent)
            assign_perm("web.is_agent_of_exporter", user, agent.main_exporter)

        user.save()

        return user

    def create_superuser(self, username: str, password: str) -> User:
        """Creat user to access django admin urls"""

        return User.objects.create_superuser(
            username=username,
            email=f"{username}@email.com",
            password=password,
            first_name=username,
            last_name=username,
            date_of_birth=datetime.date(2000, 1, 1),
            security_question="admin",
            security_answer="admin",
        )

    def _assign_permission(self, user, permission_codename):
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)
