import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.management.commands.utils.load_data import load_app_test_data
from web.models import (
    Exporter,
    ExporterAccessRequest,
    ImportApplicationType,
    Importer,
    ImporterAccessRequest,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
    Office,
    PersonalEmail,
    Task,
    User,
)
from web.permissions import ExporterObjectPermissions, ImporterObjectPermissions
from web.tests.organisations import TEST_EXPORTERS, TEST_IMPORTERS
from web.tests.types import (
    AgentExporter,
    AgentImporter,
    ExporterContact,
    ImporterContact,
    TestExporter,
    TestImporter,
)


class Command(BaseCommand):
    help = """Add test data, called when running unit tests."""

    def handle(self, *args, **options):
        if settings.APP_ENV != "test":
            raise CommandError("Can only add test data in 'test' environment!")

        # Assume data is fine if the first user is already created.
        if User.objects.filter(username="I1_main_contact").exists():
            self.stdout.write("Test data already created.")

            return

        self.stdout.write("Adding test data for unit tests.")

        load_app_test_data()

        # Access requests
        access_user = self.create_user("access_request_user")
        PersonalEmail.objects.create(
            user=access_user,
            email=access_user.email,
            portal_notifications=True,
        )

        self.create_import_access_request(access_user)
        self.create_export_access_request(access_user)

        # Create importers/exporters, agents and contacts
        self.create_test_importers()
        self.create_test_exporters()

        # ILB Admin/Caseworker
        self.create_icms_admin_user("ilb_admin_user")

        # enable disabled application types
        ImportApplicationType.objects.filter(
            type__in=[
                ImportApplicationType.Types.DEROGATION,
                ImportApplicationType.Types.OPT,
                ImportApplicationType.Types.SPS,
                ImportApplicationType.Types.TEXTILES,
            ]
        ).update(is_active=True)

        group = ObsoleteCalibreGroup.objects.create(name="Group 1", order=1)
        ObsoleteCalibre.objects.create(calibre_group=group, name="9mm", order=1)

    def create_test_importers(self) -> None:
        for imp in TEST_IMPORTERS:
            importer_obj = self.create_importer_record(imp)

            for contact in imp.contacts:
                self.create_organisation_contact(contact, importer_obj, ImporterObjectPermissions)

            for agent in imp.agents:
                agent_obj = self.create_importer_record(agent, importer_obj)

                for contact in agent.contacts:
                    self.create_organisation_contact(
                        contact, agent_obj, ImporterObjectPermissions, importer_obj
                    )

    def create_test_exporters(self) -> None:
        for exp in TEST_EXPORTERS:
            exporter_obj = self.create_exporter_record(exp)

            for contact in exp.contacts:
                self.create_organisation_contact(contact, exporter_obj, ExporterObjectPermissions)

            for agent in exp.agents:
                agent_obj = self.create_exporter_record(agent, exporter_obj)

                for contact in agent.contacts:
                    self.create_organisation_contact(
                        contact, agent_obj, ExporterObjectPermissions, exporter_obj
                    )

    @staticmethod
    def create_importer_record(
        imp: TestImporter | AgentImporter, main_importer: Importer | None = None
    ) -> Importer:
        importer_obj = Importer.objects.create(
            name=imp.importer_name,
            eori_number=imp.eori_number if isinstance(imp, TestImporter) else None,
            type=imp.type,
            region_origin=imp.region,
            main_importer=main_importer,
        )

        importer_offices = [
            Office.objects.create(
                address_1=o.address_1,
                address_2=o.address_2,
                eori_number=o.eori_number,
                postcode=o.postcode,
            )
            for o in imp.offices
        ]
        importer_obj.offices.set(importer_offices)

        return importer_obj

    @staticmethod
    def create_exporter_record(
        exp: TestExporter | AgentExporter, main_exporter: Exporter | None = None
    ) -> Exporter:
        exporter_obj = Exporter.objects.create(
            name=exp.exporter_name,
            registered_number=exp.registered_number,
            main_exporter=main_exporter,
        )

        exporter_offices = [
            Office.objects.create(
                address_1=o.address_1,
                address_2=o.address_2,
                postcode=o.postcode,
            )
            for o in exp.offices
        ]
        exporter_obj.offices.set(exporter_offices)

        return exporter_obj

    def create_organisation_contact(
        self,
        contact: ImporterContact | ExporterContact,
        org: Importer | Exporter,
        obj_perms: type[ImporterObjectPermissions | ExporterObjectPermissions],
        main_org: Importer | Exporter | None = None,
    ) -> None:
        user = self.create_user(contact.username)

        PersonalEmail.objects.create(
            user=user,
            email=f"{contact.username}@example.com",  # /PS-IGNORE
            portal_notifications=True,
        )

        group = Group.objects.get(name=obj_perms.get_group_name())
        user.groups.add(group)

        for perm in contact.permissions:
            assign_perm(perm, user, org)

        # We are creating an agent contact if main_org is set
        if main_org:
            assign_perm(obj_perms.is_agent, user, main_org)

    @staticmethod
    def create_user(username):
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

    def create_import_access_request(self, user):
        iar, _ = ImporterAccessRequest.objects.get_or_create(
            process_type=ImporterAccessRequest.PROCESS_TYPE,
            request_type="MAIN_IMPORTER_ACCESS",
            status="SUBMITTED",
            submitted_by=user,
            last_updated_by=user,
            reference="iar/1",
        )

        iar.tasks.create(is_active=True, task_type=Task.TaskType.PROCESS)

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

        ear.tasks.create(is_active=True, task_type=Task.TaskType.PROCESS)

        return ear

    def create_icms_admin_user(self, username):
        user = self.create_user(username)

        group = Group.objects.get(name="ILB Case Officer")
        user.groups.add(group)

        return user
