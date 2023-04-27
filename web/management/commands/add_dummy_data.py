import datetime
from collections.abc import Collection
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.management.commands.utils.load_data import load_app_test_data
from web.models import (
    CertificateApplicationTemplate,
    ExportApplicationType,
    Exporter,
    ImportApplicationType,
    Importer,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
    Office,
    User,
)
from web.permissions import Perms


class Command(BaseCommand):
    help = """Add dummy data. For development use only."""

    # Keeps a track of usernames created.
    users_created: list[str] = []

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

        # Load groups we want to assign to test users:
        ilb_admin_group = Group.objects.get(name="ILB Case Officer")
        importer_user_group = Group.objects.get(name="Importer User")
        exporter_user_group = Group.objects.get(name="Exporter User")

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
        importer_one_agent_one = Importer.objects.create(
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
        importer_one_agent_one.offices.add(office)

        # Second agent for importer
        importer_one_agent_two = Importer.objects.create(
            is_active=True,
            name="Dummy agent 2 for importer",
            registered_number="123",
            type=Importer.ORGANISATION,
            main_importer=importer,
        )
        office = Office.objects.create(
            is_active=True,
            address_1="Some other office road",
            address_2="London",
            postcode="WT6 2AL",  # /PS-IGNORE
        )
        importer_one_agent_two.offices.add(office)

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
            last_name="Smith (ilb_admin, importer_user_group, exporter_user_group)",
            groups=[ilb_admin_group, importer_user_group, exporter_user_group],
            linked_importers=[importer],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="ilb_admin_2",
            password=options["password"],
            first_name="Samantha",
            last_name="Stevens (ilb_admin)",
            groups=[ilb_admin_group],
            linked_importers=[importer],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="importer_user",
            password=options["password"],
            first_name="Dave",
            last_name="Jones (importer_user)",
            groups=[importer_user_group],
            linked_importers=[importer],
        )

        exporter_user = self.create_user(
            username="exporter_user",
            password=options["password"],
            first_name="Sally",
            last_name="Davis (exporter_user)",
            groups=[exporter_user_group],
            linked_exporters=[exporter],
        )

        self.create_user(
            username="agent",
            password=options["password"],
            first_name="Cameron",
            last_name="Hasra (agent)",
            groups=[importer_user_group, exporter_user_group],
            linked_importer_agents=[importer_one_agent_one, importer_one_agent_two],
            linked_exporter_agents=[agent_exporter],
        )

        self.create_superuser("admin", options["password"])

        self.stdout.write(
            f"Created following users: {', '.join([repr(u) for u in self.users_created])}"
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
        groups: Collection[Group] = (),
        linked_importers: Collection[Importer] = (),
        linked_exporters: Collection[Exporter] = (),
        linked_importer_agents: Collection[Importer] = (),
        linked_exporter_agents: Collection[Exporter] = (),
    ) -> User:
        """Create normal system users"""

        self.users_created.append(username)

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

        if groups:
            user.groups.set(groups)

        for importer in linked_importers:
            assign_perm(Perms.obj.importer.view, user, importer)
            assign_perm(Perms.obj.importer.edit, user, importer)
            assign_perm(Perms.obj.importer.manage_contacts_and_agents, user, importer)
            assign_perm(Perms.obj.importer.is_contact, user, importer)

        for exporter in linked_exporters:
            assign_perm(Perms.obj.exporter.view, user, exporter)
            assign_perm(Perms.obj.exporter.edit, user, exporter)
            assign_perm(Perms.obj.exporter.manage_contacts_and_agents, user, exporter)
            assign_perm(Perms.obj.exporter.is_contact, user, exporter)

        for agent in linked_importer_agents:
            assign_perm(Perms.obj.importer.view, user, agent)
            assign_perm(Perms.obj.importer.edit, user, agent)
            assign_perm(Perms.obj.importer.manage_contacts_and_agents, user, agent)
            assign_perm(Perms.obj.importer.is_contact, user, agent)
            assign_perm(Perms.obj.importer.is_agent, user, agent.get_main_org())

        for agent in linked_exporter_agents:
            assign_perm(Perms.obj.exporter.view, user, agent)
            assign_perm(Perms.obj.exporter.edit, user, agent)
            assign_perm(Perms.obj.exporter.manage_contacts_and_agents, user, agent)
            assign_perm(Perms.obj.exporter.is_contact, user, agent)
            assign_perm(Perms.obj.exporter.is_agent, user, agent.get_main_org())

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
