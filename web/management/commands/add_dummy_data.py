import datetime
from collections.abc import Collection
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.domains.case.export.models import ExportApplicationType
from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.management.commands.utils.load_data import load_app_test_data
from web.models import ImportApplicationType, ObsoleteCalibre, ObsoleteCalibreGroup


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

        load_app_test_data()

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
            is_active=True,
            address_1="Buckingham Palace",
            address_2="London",
            postcode="SW1A 1AA",  # /PS-IGNORE
        )
        exporter.offices.add(office)

        office = Office.objects.create(
            is_active=True,
            address_1="209 Roden St",
            address_2="Belfast",
            postcode="BT12 5QB",  # /PS-IGNORE
        )
        exporter.offices.add(office)

        # importer
        importer = Importer.objects.create(
            is_active=True,
            name="Dummy importer",
            registered_number="84",
            eori_number="GB123456789012345",
            type=Importer.ORGANISATION,
        )

        office = Office.objects.create(
            is_active=True,
            address_1="3 Whitehall Pl",
            address_2="Westminster",
            address_3="London",
            postcode="SW1A 2HP",  # /PS-IGNORE
        )
        importer.offices.add(office)

        office = Office.objects.create(
            is_active=True,
            address_1="902 Some place",
            address_2="Belfast",
            postcode="BT12 5QB",  # /PS-IGNORE
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
            is_active=True,
            address_1="Some office road",
            address_2="London",
            postcode="WT6 2AL",  # /PS-IGNORE
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
            is_active=True,
            address_1="14 some way",
            address_2="Townsville",
            postcode="S44 3SS",  # /PS-IGNORE
        )
        agent_exporter.offices.add(office)

        self.stdout.write("Created dummy agent for importer/exporter")

        ilb_admin_user = self.create_user(
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

        exporter_user = self.create_user(
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

        create_certificate_application_templates(ilb_admin_user)
        create_certificate_application_templates(exporter_user)

        group = ObsoleteCalibreGroup.objects.create(name="Group 1", order=1)
        ObsoleteCalibre.objects.create(calibre_group=group, name="9mm", order=1)

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
            email=f"{username}@email.com",  # /PS-IGNORE
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
            email=f"{username}@email.com",  # /PS-IGNORE
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


def create_certificate_application_templates(
    owner: User,
) -> list[CertificateApplicationTemplate]:
    data = {
        "GMP": {
            "is_responsible_person": "yes",
            "responsible_person_name": f"{owner.first_name}",
            "responsible_person_address": "Old Admiralty Building\nLondon\n",
        },
        "COM": {
            "product_name": "Acme Wonder Product",
            "is_manufacturer": True,
        },
    }
    objs = []

    for type_code, label in ExportApplicationType.Types.choices:
        objs.append(
            CertificateApplicationTemplate(
                name=f"{label} template ({type_code})",
                description=f"Description of {label} template",
                application_type=type_code,
                sharing=CertificateApplicationTemplate.SharingStatuses.PRIVATE,
                data=data.get(type_code, {}),
                owner=owner,
            )
        )

    return CertificateApplicationTemplate.objects.bulk_create(objs)
