import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm

from web.management.commands.utils.load_data import load_app_test_data
from web.models import (
    Constabulary,
    ExportApplicationType,
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
from web.permissions import (
    ExporterObjectPermissions,
    ImporterObjectPermissions,
    constabulary_add_contact,
)
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
        add_personal_email(access_user)

        self.create_import_access_request(access_user)
        self.create_export_access_request(access_user)

        # Create importers/exporters, agents and contacts
        self.create_test_importers()
        self.create_test_exporters()

        # ICMS Caseworkers (ILB, NCA & HO)
        self.create_icms_admin_user("ilb_admin_user")
        self.create_icms_admin_user("ilb_admin_two")
        self.create_nca_admin_user("nca_admin_user")
        self.create_ho_admin_user("ho_admin_user")
        self.create_san_admin_user("san_admin_user")
        self.create_con_user(
            "con_user", linked_constabularies=["Nottingham", "Lincolnshire", "Derbyshire"]
        )

        # enable disabled application types
        ImportApplicationType.objects.update(is_active=True)
        ExportApplicationType.objects.update(is_active=True)

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
            is_active=imp.is_active,
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
            is_active=exp.is_active,
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
        user = self.create_user(contact.username, contact.is_active)
        add_personal_email(user)
        add_group(user, obj_perms.get_group_name())

        for perm in contact.permissions:
            assign_perm(perm, user, org)

        # We are creating an agent contact if main_org is set
        if main_org:
            assign_perm(obj_perms.is_agent, user, main_org)

    @staticmethod
    def create_user(username, is_active=True):
        return User.objects.create_user(
            username=username,
            password="test",
            is_superuser=False,
            is_active=is_active,
            email=f"{username}@example.com",  # /PS-IGNORE
            first_name=f"{username}_first_name",
            last_name=f"{username}_last_name",
            date_of_birth=datetime.date(2000, 1, 1),
            job_title=f"{username}_job_title",
            organisation=f"{username}_org",
            department=f"{username}_dep",
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
        add_personal_email(user)
        add_group(user, "ILB Case Officer")

        return user

    def create_nca_admin_user(self, username):
        user = self.create_user(username)
        add_personal_email(user)
        add_group(user, "NCA Case Officer")

        return user

    def create_ho_admin_user(self, username):
        user = self.create_user(username)
        add_personal_email(user)
        add_group(user, "Home Office Case Officer")

        return user

    def create_san_admin_user(self, username):
        user = self.create_user(username)
        add_personal_email(user)
        add_group(user, "Sanctions Case Officer")

        return user

    def create_con_user(self, username, linked_constabularies: list[str]):
        user = self.create_user(username)
        add_personal_email(user)

        for con in linked_constabularies:
            constabulary = Constabulary.objects.get(name=con)
            constabulary_add_contact(constabulary, user)


def add_personal_email(user):
    PersonalEmail.objects.create(user=user, email=user.email, portal_notifications=True)


def add_group(user, group_name):
    group = Group.objects.get(name=group_name)
    user.groups.add(group)
