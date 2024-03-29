import datetime as dt
from collections.abc import Collection
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from web.domains.country.models import Country
from web.management.commands.utils.load_data import load_app_test_data
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    CFSScheduleTemplate,
    Constabulary,
    Email,
    ExportApplicationType,
    Exporter,
    FirearmsAct,
    ImportApplicationType,
    Importer,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
    Office,
    ProductLegislation,
    Section5Clause,
    Signature,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import constabulary_add_contact, organisation_add_contact
from web.utils.s3 import upload_file_obj_to_s3


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
        nca_case_officer = Group.objects.get(name="NCA Case Officer")
        ho_case_officer = Group.objects.get(name="Home Office Case Officer")
        san_case_officer = Group.objects.get(name="Sanctions Case Officer")
        import_search_user = Group.objects.get(name="Import Search User")
        report_user = Group.objects.get(name="Report User")

        # Enable disabled application types to test / develop them
        if settings.SET_INACTIVE_APP_TYPES_ACTIVE:
            ImportApplicationType.objects.update(is_active=True)
            ExportApplicationType.objects.update(is_active=True)

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
            last_name="Smith (ilb_admin)",
            groups=[ilb_admin_group],
        )

        self.create_user(
            username="ilb_admin_2",
            password=options["password"],
            first_name="Samantha",
            last_name="Stevens (ilb_admin)",
            groups=[ilb_admin_group],
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
            username="importer_agent",
            password=options["password"],
            first_name="Cameron",
            last_name="Hasra (agent)",
            groups=[importer_user_group],
            linked_importer_agents=[importer_one_agent_one, importer_one_agent_two],
        )

        self.create_user(
            username="exporter_agent",
            password=options["password"],
            first_name="Marie",
            last_name="Jacobs (agent)",
            groups=[exporter_user_group],
            linked_exporter_agents=[agent_exporter],
        )

        self.create_user(
            username="nca_admin",
            password=options["password"],
            first_name="Clara",
            last_name="Boone (NCA Case Officer)",
            groups=[nca_case_officer],
        )

        self.create_user(
            username="ho_admin",
            password=options["password"],
            first_name="Steven",
            last_name="Hall (HO Case Officer)",
            groups=[ho_case_officer],
        )

        self.create_user(
            username="san_admin",
            password=options["password"],
            first_name="Karen",
            last_name="Bradley (SAN Case Officer)",
            groups=[san_case_officer],
        )

        self.create_user(
            username="san_admin_2",
            password=options["password"],
            first_name="Emilio",
            last_name="Mcgee (SAN Case Officer)",
            groups=[san_case_officer],
        )

        self.create_user(
            username="con_user",
            password=options["password"],
            first_name="Colin",
            last_name="Baker",
            linked_constabularies=Constabulary.objects.filter(
                name__in=["Nottingham", "Lincolnshire", "Derbyshire"]
            ),
        )

        self.create_user(
            username="import_search_user",
            password=options["password"],
            first_name="Hercule",
            last_name="Poirot (Import Search User)",
            groups=[import_search_user],
        )

        self.create_user(
            username="report_user",
            password=options["password"],
            first_name="Neville",
            last_name="Southall (Report User)",
            groups=[report_user],
        )

        #
        # Add some fake V1 migrated users.
        self.create_user(
            username="migrated-user-1@example.com",  # /PS-IGNORE
            password=options["password"],
            first_name="Bill",
            last_name="Wesley (importer_user)",
            groups=[importer_user_group],
            linked_importers=[importer],
            icms_v1_user=True,
        )

        self.create_user(
            username="migrated-user-2@example.com",  # /PS-IGNORE
            password=options["password"],
            first_name="Dani",
            last_name="Winslow (exporter_user)",
            groups=[exporter_user_group],
            linked_importers=[exporter],
            icms_v1_user=True,
        )

        self.create_superuser("admin", options["password"])

        self.stdout.write(
            f"Created following users: {', '.join([repr(u) for u in self.users_created])}"
        )
        self.stdout.write("Created following superusers: 'admin'")

        create_certificate_application_templates(exporter_user)

        group = ObsoleteCalibreGroup.objects.create(name="Group 1", order=1)
        ObsoleteCalibre.objects.create(calibre_group=group, name="9mm", order=1)

        create_dummy_signature(ilb_admin_user)

        # Add a few dummy section 5 clauses (The real values will come from the data migration)
        Section5Clause.objects.create(
            clause="5(1A)(a)", description="Test value 1", created_by=ilb_admin_user
        )
        Section5Clause.objects.create(
            clause="5(1A)(b)", description="Test value 2", created_by=ilb_admin_user
        )
        Section5Clause.objects.create(
            clause="5(1A)(c)", description="Test value 3", created_by=ilb_admin_user
        )

        # Add some Firearm acts (Copied from data migration)
        FirearmsAct.objects.bulk_create(
            [
                FirearmsAct(created_by=ilb_admin_user, act=act)
                for act in [
                    "Section 1 Firearms",
                    "Section 1 Shotguns",
                    "Section 2 Shotguns",
                    "Section 1 Component Parts",
                    "Section 1 Ammunition",
                    "Expanding Ammunition 5(1A)(f)",
                    "Suppressors",
                ]
            ]
        )

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
        linked_constabularies: Collection[Constabulary] = (),
        icms_v1_user: bool = False,
    ) -> User:
        """Create normal system users"""

        self.users_created.append(username)

        user = User.objects.create_user(
            username=username,
            password=password,
            is_superuser=False,
            is_active=True,
            email=f"{username}@example.com",  # /PS-IGNORE
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dt.date(2000, 1, 1),
            icms_v1_user=icms_v1_user,
        )

        Email.objects.create(
            email=f"{username}@example.com",  # /PS-IGNORE
            is_primary=True,
            portal_notifications=True,
            type=Email.WORK,
            user=user,
        )

        if groups:
            user.groups.set(groups)

        for importer in linked_importers:
            organisation_add_contact(importer, user, assign_manage=True)

        for exporter in linked_exporters:
            organisation_add_contact(exporter, user, assign_manage=True)

        for agent in linked_importer_agents:
            organisation_add_contact(agent, user)

        for agent in linked_exporter_agents:
            organisation_add_contact(agent, user)

        for constabulary in linked_constabularies:
            constabulary_add_contact(constabulary, user)

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
            date_of_birth=dt.date(2000, 1, 1),
        )


def create_certificate_application_templates(
    owner: User,
) -> list[CertificateApplicationTemplate]:
    #
    # Add a COM template.
    com_cat = CertificateApplicationTemplate.objects.create(
        name="Test COM Template",
        description="description",
        application_type=ExportApplicationType.Types.MANUFACTURE,
        sharing=CertificateApplicationTemplate.SharingStatuses.EDIT,
        owner=owner,
    )
    CertificateOfManufactureApplicationTemplate.objects.create(
        template=com_cat,
        is_pesticide_on_free_sale_uk=True,
        is_manufacturer=True,
        product_name="Test product_name",
        chemical_name="Test chemical_name",
        manufacturing_process="Test manufacturing_process",
    )

    #
    # Add a CFS template.
    cfs_cat = CertificateApplicationTemplate.objects.create(
        name="Test CFS Template",
        description="description",
        application_type=ExportApplicationType.Types.FREE_SALE,
        sharing=CertificateApplicationTemplate.SharingStatuses.EDIT,
        owner=owner,
    )
    cfs_template = CertificateOfFreeSaleApplicationTemplate.objects.create(template=cfs_cat)
    cfs_schedule_template = CFSScheduleTemplate.objects.create(
        application=cfs_template,
        exporter_status=CFSScheduleTemplate.ExporterStatus.IS_MANUFACTURER,
        brand_name_holder=YesNoChoices.yes,
    )
    cfs_schedule_template.legislations.add(ProductLegislation.objects.first())

    for i in range(1, 6):
        product = cfs_schedule_template.products.create(product_name=f"Test Product {i}")
        for z in range(1, i + 1):
            product.product_type_numbers.create(product_type_number=z)
            # e.g. 111-11-1111
            z = str(z)  # type:ignore[assignment]
            cas = f"{z * 3}-{z * 2}-{z * 4}"
            product.active_ingredients.create(name=f"Test Ingredient {z}", cas_number=cas)

    #
    # Add a GMP template
    gmp_cat = CertificateApplicationTemplate.objects.create(
        name="Test GMP Template",
        description="description",
        application_type=ExportApplicationType.Types.GMP,
        sharing=CertificateApplicationTemplate.SharingStatuses.EDIT,
        owner=owner,
    )
    gmp_template = CertificateOfGoodManufacturingPracticeApplicationTemplate.objects.create(
        template=gmp_cat,
        brand_name="Test Brand name",
        is_responsible_person=YesNoChoices.yes,
        responsible_person_name="Test responsible person name",
    )
    gmp_template.countries.add(Country.objects.get(name="China"))

    return [com_cat, cfs_cat, gmp_cat]


def create_dummy_signature(user: User) -> None:
    """Creates a dummy active signature object to appear in licence and certificate documents"""
    file_path = settings.BASE_DIR / "web/static/web/img/dit-no-signature.png"

    if not file_path.is_file():
        raise CommandError("Dummy signature file missing")

    filename = "active_dummy_signature.png"
    key = f"dummy_signature/{filename}"
    file_size = upload_file_obj_to_s3(file_path.open("rb"), key)

    Signature.objects.create(
        name="Active Dummy Signature",
        signatory="Import Licencing Branch",
        history=f"Created by add_dummy_data command on {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        filename=filename,
        path=key,
        content_type="image/png",
        created_by=user,
        file_size=file_size,
        is_active=True,
    )
