import datetime

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.domains.case.access.models import ExporterAccessRequest, ImporterAccessRequest
from web.domains.exporter.models import Exporter
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

        # Access requests
        access_user = self.create_access_user("test_access_user")
        self.create_import_access_request(access_user)
        self.create_export_access_request(access_user)

        # Importer
        importer = self.create_importer()
        self.create_importer_user(importer, "test_import_user")
        self.create_importer_user(importer, "importer_contact")

        agent_importer = self.create_importer(
            main_importer=importer, name="UK based agent importer"
        )
        self.create_agent_importer_user(importer, agent_importer, "test_agent_import_user")

        # Exporter
        exporter = self.create_exporter()
        self.create_exporter_user(exporter, "test_export_user")

        agent_exporter = self.create_exporter(
            main_exporter=exporter, name="UK based agent exporter"
        )
        self.create_agent_exporter_user(exporter, agent_exporter, "test_agent_export_user")

        # ILB Admin/Case worker
        self.create_icms_admin_user("test_icms_admin_user")

        # enable disabled application types
        ImportApplicationType.objects.filter(
            type__in=[
                ImportApplicationType.Types.DEROGATION,
                ImportApplicationType.Types.OPT,
                ImportApplicationType.Types.SPS,
                ImportApplicationType.Types.TEXTILES,
            ]
        ).update(is_active=True)

    def create_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return User.objects.create_user(
                username=username,
                password="test",
                password_disposition=User.FULL,
                is_superuser=False,
                account_status=User.ACTIVE,
                is_active=True,
                email=f"{username}@email.com",  # /PS-IGNORE
                first_name=f"{username}_first_name",
                last_name=f"{username}_last_name",
                date_of_birth=datetime.date(2000, 1, 1),
                security_question="security_question",
                security_answer="security_answer",
            )

        return user

    def create_access_user(self, username):
        return self.create_user(username)

    def create_import_access_request(self, user):
        iar, _ = ImporterAccessRequest.objects.get_or_create(
            process_type=ImporterAccessRequest.PROCESS_TYPE,
            request_type="MAIN_IMPORTER_ACCESS",
            status="SUBMITTED",
            submitted_by=user,
            last_updated_by=user,
            reference="iar/1",
        )

        return iar

    def create_export_access_request(self, user):
        ear, _ = ExporterAccessRequest.objects.get_or_create(
            process_type=ExporterAccessRequest.PROCESS_TYPE,
            request_type="MAIN_EXPORTER_ACCESS",
            status="SUBMITTED",
            submitted_by=user,
            last_updated_by=user,
            reference="ear/1",
        )

        return ear

    def create_importer_user(self, importer, username):
        user = self.create_user(username)

        self._assign_permission(user, "importer_access")
        assign_perm("web.is_contact_of_importer", user, importer)

        return user

    def create_exporter_user(self, exporter, username):
        user = self.create_user(username)

        self._assign_permission(user, "exporter_access")
        assign_perm("web.is_contact_of_exporter", user, exporter)

        return user

    def create_agent_importer_user(self, importer, agent, username):
        user = self.create_user(username)

        self._assign_permission(user, "importer_access")
        assign_perm("web.is_contact_of_importer", user, agent)
        assign_perm("web.is_agent_of_importer", user, importer)

        return user

    def create_agent_exporter_user(self, exporter, agent, username):
        user = self.create_user(username)

        self._assign_permission(user, "exporter_access")
        assign_perm("web.is_contact_of_exporter", user, agent)
        assign_perm("web.is_agent_of_exporter", user, exporter)

        return user

    def create_icms_admin_user(self, username):
        user = self.create_user(username)

        for perm in [
            "importer_access",
            "exporter_access",
            "ilb_admin",
            "mailshot_access",
        ]:
            self._assign_permission(user, perm)

        return user

    def create_importer(self, main_importer=None, name="UK based importer"):
        office, _ = Office.objects.get_or_create(
            is_active=True, address="47 some way, someplace", postcode="BT180LZ"  # /PS-IGNORE
        )

        importer, created = Importer.objects.get_or_create(
            is_active=True,
            type=Importer.INDIVIDUAL,
            region_origin=Importer.UK,
            name=name,
            main_importer=main_importer,
        )

        if created:
            importer.offices.add(office)

        return importer

    def create_exporter(self, main_exporter=None, name="UK based exporter"):
        office, _ = Office.objects.get_or_create(
            is_active=True, address="47 some way, someplace", postcode="S410SG"  # /PS-IGNORE
        )

        exporter, created = Exporter.objects.get_or_create(
            is_active=True,
            name=name,
            registered_number="422",
            main_exporter=main_exporter,
        )

        if created:
            exporter.offices.add(office)

        return exporter

    def _assign_permission(self, user, permission_codename):
        permission = Permission.objects.get(codename=permission_codename)
        user.user_permissions.add(permission)
