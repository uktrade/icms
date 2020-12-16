from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from guardian.shortcuts import assign_perm

from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User


class Command(BaseCommand):
    help = """Create an exporter associated with an Export Company"""

    def add_arguments(self, parser):
        parser.add_argument("--first-name", dest="first_name", nargs="?", default="Ada")
        parser.add_argument("--last-name", dest="last_name", nargs="?", default="Lovelace")
        parser.add_argument("--title", nargs="?", default="Ms")

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
        user.user_permissions.add(Permission.objects.get(codename="exporter_access"))
        user.save()

        exporter = Exporter.objects.create(
            is_active=True, name=f"{username} org", registered_number="42"
        )
        assign_perm("web.is_contact_of_exporter", user, exporter)

        office = Office.objects.create(
            is_active=True, postcode="SW1A 2HP", address="3 Whitehall Pl, Westminster, London"
        )
        exporter.offices.add(office)
        self.stdout.write(f"Created exporter user with login/pass: {username}/password")
