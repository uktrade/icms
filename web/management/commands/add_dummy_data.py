import datetime

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

    def handle(self, *args, **options):
        if settings.APP_ENV not in ("local", "dev"):
            raise CommandError("Can only add dummy data in 'dev' / 'local' environments!")

        # enable disabled application types so we can test/develop them
        ImportApplicationType.objects.filter(
            type__in=[
                ImportApplicationType.Types.OPT,
                ImportApplicationType.Types.TEXTILES,
            ]
        ).update(is_active=True)

        user = User.objects.create_superuser(
            username="admin",
            email="admin@blaa.com",
            password=options["password"],
            first_name="admin",
            last_name="admin",
            date_of_birth=datetime.date(2000, 1, 1),
            security_question="admin",
            security_answer="admin",
        )

        self.stdout.write("Created following users: admin")

        # permissions
        for perm in [
            "importer_access",
            "exporter_access",
            "reference_data_access",
            "mailshot_access",
        ]:
            user.user_permissions.add(Permission.objects.get(codename=perm))

        user.save()

        # exporter
        exporter = Exporter.objects.create(
            is_active=True, name="Dummy exporter", registered_number="42"
        )
        assign_perm("web.is_contact_of_exporter", user, exporter)

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
            type=Importer.ORGANISATION,
        )
        assign_perm("web.is_contact_of_importer", user, importer)

        office = Office.objects.create(
            is_active=True, postcode="SW1A 2HP", address="3 Whitehall Pl, Westminster, London"
        )
        importer.offices.add(office)

        office = Office.objects.create(
            is_active=True, postcode="BT12 5QB", address="209 Roden St, Belfast"
        )
        importer.offices.add(office)

        self.stdout.write("Created dummy importer/exporter and associated admin user with them")
