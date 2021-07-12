import datetime

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.models import ImportApplicationType


class Command(BaseCommand):
    help = """Add test data, called when running unit tests."""

    def handle(self, *args, **options):
        if settings.APP_ENV != "test":
            raise CommandError("Can only add test data in 'test' environment!")

        # Assume data is fine if the first user is already created.
        if User.objects.filter(username="test_import_user").exists():
            self.stdout.write("Test data already created.")

            return

        self.stdout.write("Adding test data for unit tests.")
        importer = self.create_importer()
        self.create_importer_user(importer, "test_import_user")
        self.create_importer_user(importer, "importer_contact")
        self.create_icms_admin_user("test_icms_admin_user")

        # enable disabled application types
        ImportApplicationType.objects.filter(
            type__in=[
                ImportApplicationType.Types.OPT,
                ImportApplicationType.Types.TEXTILES,
                ImportApplicationType.Types.SPS,
            ]
        ).update(is_active=True)

    def create_importer_user(self, importer, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                password="test",
                password_disposition=User.FULL,
                is_superuser=False,
                account_status=User.ACTIVE,
                is_active=True,
                email=f"{username}@email.com",
                first_name=f"{username}_first_name",
                last_name=f"{username}_last_name",
                date_of_birth=datetime.date(2000, 1, 1),
                security_question="security_question",
                security_answer="security_answer",
            )
            self._assign_permission(user, "importer_access")
            assign_perm("web.is_contact_of_importer", user, importer)
            user.save()

        return user

    def create_icms_admin_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                password="test",
                password_disposition=User.FULL,
                is_superuser=False,
                account_status=User.ACTIVE,
                is_active=True,
                email=f"{username}@email.com",
                first_name=f"{username}_first_name",
                last_name=f"{username}_last_name",
                date_of_birth=datetime.date(2000, 1, 1),
                security_question="security_question",
                security_answer="security_answer",
            )

            for perm in [
                "importer_access",
                "exporter_access",
                "reference_data_access",
                "mailshot_access",
            ]:
                self._assign_permission(user, perm)

            user.save()

        return user

    def create_importer(self):
        office, _ = Office.objects.get_or_create(
            is_active=True, address="47 some way, someplace", postcode="S410SG"
        )

        importer, created = Importer.objects.get_or_create(
            is_active=True,
            type=Importer.INDIVIDUAL,
            region_origin=Importer.UK,
            name="UK based importer",
        )

        if created:
            importer.offices.add(office)

        return importer

    def _assign_permission(self, user, permission_codename):
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)
