from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from guardian.shortcuts import assign_perm

from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User


class Command(BaseCommand):
    help = """Create an importer associated with an Import Company"""

    def add_arguments(self, parser):
        parser.add_argument("--first-name", dest="first_name", nargs="?", default="Guido")
        parser.add_argument("--last-name", dest="last_name", nargs="?", default="van Rossum")
        parser.add_argument("--title", nargs="?", default="Mr")

    def handle(self, *args, **kwargs):
        username = f"{kwargs['first_name']}{kwargs['last_name']}".strip().lower().replace(" ", "")

        user = User.objects.create(
            username=username,
            first_name=kwargs["first_name"],
            last_name=kwargs["last_name"],
            email=f"{username}@example.com",
            is_active=True,
            title=kwargs["title"],
            password_disposition=User.FULL,
        )
        user.set_password("password")
        user.user_permissions.add(Permission.objects.get(codename="importer_access"))
        user.save()

        exporter = Importer.objects.create(
            is_active=True,
            name=f"{username} org",
            registered_number="42",
            type=Importer.ORGANISATION,
        )
        assign_perm("web.is_contact_of_importer", user, exporter)

        office = Office.objects.create(
            is_active=True, postcode="SW1A 2HP", address="3 Whitehall Pl, Westminster, London",
        )
        exporter.offices.add(office)
        self.stdout.write(f"Created importer user with login/pass: {username}/password")
