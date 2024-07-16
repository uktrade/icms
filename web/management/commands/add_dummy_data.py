import datetime as dt
from collections.abc import Collection
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

from web.domains.country.models import Country
from web.management.commands.utils.load_data import load_app_test_data
from web.models import (
    ActQuantity,
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    CFSScheduleTemplate,
    ClauseQuantity,
    Constabulary,
    Email,
    ExportApplicationType,
    Exporter,
    File,
    FirearmsAct,
    FirearmsAuthority,
    ImportApplicationType,
    Importer,
    Office,
    ProductLegislation,
    Section5Authority,
    Section5Clause,
    Signature,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import constabulary_add_contact, organisation_add_contact
from web.utils.s3 import upload_file_obj_to_s3

IMPORT_USERS = [
    # importer_user / importer_agent
    {
        "first_name": "Dave",
        "last_name": "Jones",
        "agent_first_name": "Cameron",
        "agent_last_name": "Hasra",
    },
    # importer_user_2 / importer_agent_2
    {
        "first_name": "Luke",
        "last_name": "Mosley",
        "agent_first_name": "Sarah",
        "agent_last_name": "Logan",
    },
    # importer_user_3 / importer_agent_3
    {
        "first_name": "Lucy",
        "last_name": "Ross",
        "agent_first_name": "Issac",
        "agent_last_name": "Campbell",
    },
    # importer_user_4 / importer_agent_4
    {
        "first_name": "James",
        "last_name": "Hall",
        "agent_first_name": "Brian",
        "agent_last_name": "Roach",
    },
    # importer_user_5 / importer_agent_5
    {
        "first_name": "Steven",
        "last_name": "Rudd",
        "agent_first_name": "Julie",
        "agent_last_name": "Dale",
    },
]

EXPORT_USERS = [
    # exporter_user / exporter_agent
    {
        "first_name": "Sally",
        "last_name": "Davis",
        "agent_first_name": "Marie",
        "agent_last_name": "Jacobs",
    },
    # exporter_user_2 / exporter_agent_2
    {
        "first_name": "Jesse",
        "last_name": "Carey",
        "agent_first_name": "Paul",
        "agent_last_name": "Adams",
    },
    # exporter_user_3 / exporter_agent_3
    {
        "first_name": "Joe",
        "last_name": "Dunn",
        "agent_first_name": "Sue",
        "agent_last_name": "Daniels",
    },
    # exporter_user_4 / exporter_agent_4
    {
        "first_name": "Vincent",
        "last_name": "Duke",
        "agent_first_name": "Ron",
        "agent_last_name": "Wilkinson",
    },
    # exporter_user_5 / exporter_agent_5
    {
        "first_name": "Angela",
        "last_name": "Young",
        "agent_first_name": "Harry",
        "agent_last_name": "Fry",
    },
]

ADMIN_USERS = [
    # ilb_admin
    {"first_name": "Ashley", "last_name": "Smith"},
    # ilb_admin_2
    {"first_name": "Samantha", "last_name": "Stevens"},
    # ilb_admin_3
    {"first_name": "Ian", "last_name": "Hughes"},
    # ilb_admin_4
    {"first_name": "Jane", "last_name": "Cross"},
    # ilb_admin_5
    {"first_name": "Drew", "last_name": "Moss"},
]


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

    def add_ilb_admin_users(self, password: str) -> None:
        ilb_admin_group = Group.objects.get(name="ILB Case Officer")
        for index, user in enumerate(ADMIN_USERS, start=1):
            ilb_admin_user = self.create_user(
                username="ilb_admin" if index == 1 else f"ilb_admin_{index}",
                password=password,
                first_name=user["first_name"],
                last_name=user["last_name"],
                groups=[ilb_admin_group],
            )
            if index == 1:
                create_dummy_signature(ilb_admin_user)
                self.add_section_five_clauses(ilb_admin_user)

    def add_exporters_and_users(self, password: str) -> None:
        exporter_user_group = Group.objects.get(name="Exporter User")
        for index, users in enumerate(EXPORT_USERS, start=1):
            exporter = Exporter.objects.create(
                is_active=True,
                name=f"Dummy exporter {index}",
                registered_number=f"4{index}",
                exclusive_correspondence=True,
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index} Buckingham Palace",
                address_2="London",
                postcode=f"SW{index}A {index}AA",  # /PS-IGNORE
            )
            exporter.offices.add(office)

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index}00 Roden St",
                address_2="Belfast",
                postcode=f"BT1{index} {index}QB",  # /PS-IGNORE
            )
            exporter.offices.add(office)

            self.stdout.write(f"Created dummy exporter {index}")

            # agent for exporter
            agent_exporter = Exporter.objects.create(
                is_active=True,
                name=f"Dummy agent exporter {index}",
                registered_number=f"42{index}",
                main_exporter=exporter,
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index} some way",
                address_2="Townsville",
                postcode=f"S4{index} 3SS",  # /PS-IGNORE
            )
            agent_exporter.offices.add(office)

            exporter_username = "exporter_user" if index == 1 else f"exporter_user_{index}"
            exporter_user = self.create_user(
                username=exporter_username,
                password=password,
                first_name=users["first_name"],
                last_name=users["last_name"],
                groups=[exporter_user_group],
                linked_exporters=[exporter],
            )
            create_certificate_application_templates(exporter_user)

            self.create_user(
                username="exporter_agent" if index == 1 else f"exporter_agent_{index}",
                password=password,
                first_name=users["agent_first_name"],
                last_name=users["agent_last_name"],
                groups=[exporter_user_group],
                linked_exporter_agents=[agent_exporter],
            )
            self.stdout.write(f"Created {exporter_username} & agent")
            if index == 1:
                self.create_user(
                    username="migrated-user-2@example.com",  # /PS-IGNORE
                    password=password,
                    first_name="Dani",
                    last_name="Winslow",
                    groups=[exporter_user_group],
                    linked_importers=[exporter],
                    icms_v1_user=True,
                )
                self.stdout.write("Created fake migrated exporter user")

    def add_importers_and_users(self, password: str) -> None:
        importer_user_group = Group.objects.get(name="Importer User")
        for index, users in enumerate(IMPORT_USERS, start=1):
            importer = Importer.objects.create(
                is_active=True,
                name=f"Dummy importer {index}",
                registered_number=f"8{index}",
                eori_number=f"GB12345678901234{index}",
                type=Importer.ORGANISATION,
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index} Whitehall Pl",
                address_2="Westminster",
                address_3="London",
                postcode=f"SW{index}A {index}HP",  # /PS-IGNORE
            )
            importer.offices.add(office)

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index}0{index} Some place",
                address_2="Belfast",
                postcode=f"BT{index}2 {index}QB",  # /PS-IGNORE
            )
            importer.offices.add(office)

            # Add verified firearms authority to importer
            firearms_authority = FirearmsAuthority.objects.create(
                importer=importer,
                reference=f"ref/{index}",
                certificate_type=FirearmsAuthority.REGISTERED_FIREARMS_DEALER,
                postcode=f"S{index}{index+1}SS",  # /PS-IGNORE
                address="Address line 1",
                address_entry_type=FirearmsAuthority.MANUAL,
                start_date=timezone.now().date(),
                end_date=dt.date(dt.date.today().year + 3, 1, 1),
                further_details="",
                issuing_constabulary=Constabulary.objects.filter(is_active=True)[index],
            )
            firearms_authority.linked_offices.set(importer.offices.all())

            for act in FirearmsAct.objects.all():
                ActQuantity.objects.create(
                    firearmsauthority=firearms_authority,
                    firearmsact=act,
                    quantity=100 * index,
                )

            ilb_admin_user = User.objects.get(username="ilb_admin")

            firearms_authority.files.add(create_dummy_file(firearms_authority, ilb_admin_user))

            # Add verified section 5 authority to importer.
            section5_authority = Section5Authority.objects.create(
                importer=importer,
                reference=f"section-5-ref/{index}",
                postcode=f"S{index}{index+1}SS",  # /PS-IGNORE
                address="Address line 1",
                address_entry_type=FirearmsAuthority.MANUAL,
                start_date=timezone.now().date(),
                end_date=dt.date(dt.date.today().year + 3, 1, 1),
                further_details="",
            )

            section5_authority.linked_offices.set(importer.offices.all())

            for clause in Section5Clause.objects.all():
                ClauseQuantity.objects.create(
                    section5authority=section5_authority,
                    section5clause=clause,
                    quantity=100 * index,
                )

            section5_authority.files.add(create_dummy_file(section5_authority, ilb_admin_user))

            self.stdout.write(f"Created dummy importer {index}")

            # agent for importer
            importer_one_agent_one = Importer.objects.create(
                is_active=True,
                name=f"Dummy agent for importer {index}",
                registered_number=f"84{index}",
                type=Importer.ORGANISATION,
                main_importer=importer,
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"{index} Some office road",
                address_2="London",
                postcode=f"WT{index} 2AL",  # /PS-IGNORE
            )
            importer_one_agent_one.offices.add(office)

            # Second agent for importer
            importer_one_agent_two = Importer.objects.create(
                is_active=True,
                name=f"Dummy agent 2 for importer {index}",
                registered_number="123",
                type=Importer.ORGANISATION,
                main_importer=importer,
            )
            office = Office.objects.create(
                is_active=True,
                address_1="Some other office road",
                address_2="London",
                postcode=f"WT{index} {index}AL",  # /PS-IGNORE
            )
            importer_one_agent_two.offices.add(office)

            importer_username = "importer_user" if index == 1 else f"importer_user_{index}"
            self.create_user(
                username=importer_username,
                password=password,
                first_name=users["first_name"],
                last_name=users["last_name"],
                groups=[importer_user_group],
                linked_importers=[importer],
            )

            self.create_user(
                username="importer_agent" if index == 1 else f"importer_agent_{index}",
                password=password,
                first_name=users["agent_first_name"],
                last_name=users["agent_last_name"],
                groups=[importer_user_group],
                linked_importer_agents=[importer_one_agent_one, importer_one_agent_two],
            )
            self.stdout.write(f"Created {importer_username} & agent")
            if index == 1:
                self.create_user(
                    username="migrated-user-1@example.com",  # /PS-IGNORE
                    password=password,
                    first_name="Bill",
                    last_name="Wesley",
                    groups=[importer_user_group],
                    linked_importers=[importer],
                    icms_v1_user=True,
                )
                self.stdout.write("Created fake migrated importer user")

    def add_section_five_clauses(self, ilb_admin_user):
        # Add a few dummy section 5 clauses (The real values will come from the data migration)
        dummy_section_5_clauses = (
            (
                "5(1)(a)",
                "Any firearm capable of burst- or fully automatic fire and component parts of these.",
            ),
            (
                "5(1)(ab)",
                "Any semi-automatic, self-loading or pump action rifled gun and carbines but not pistols.",
            ),
            (
                "5(1)(aba)",
                "Any firearm with a barrel less than 30 cm long or which is less than 60 cm long"
                " overall - short firearms (pistols and revolvers) and component parts of these.",
            ),
            (
                "5(1)(ac)",
                "Any pump-action or self-loading shotgun with a barrel less than 24 inches long or which is less than 40 inches long overall.",
            ),
            ("5(1)(ad)", " Any smoothbore revolver gun except 9mm rim fire or muzzle loaded."),
            (
                "5(1)(ae)",
                "Any rocket launcher or mortar which fires a stabilised missile other than for line throwing, pyrotechnics or signalling.",
            ),
            ("5(1)(af)", " Any firearm using a self-contained gas cartridge system."),
            (
                "5(1)(b)",
                "Any weapon designed or adapted to discharge noxious liquid, gas or other thing.",
            ),
            (
                "5(1)(c)",
                "Any cartridge with an explosive bullet or any ammo designed to discharge any "
                "noxious thing (as described above) and if capable of being used with a firearm of"
                " any description, any grenade, bomb or other like missile, rocket or shell designed to explode.",
            ),
            ("5(1A)(b)", " Explosive rockets or ammunition not covered in 5(1)(c)"),
            (
                "5(1A)(c)",
                "Any launcher or projector not covered in 5(1)(ae) designed to fire any rocket or ammunition covered by 5(1A)(b) or 5(1)(c).",
            ),
            ("5(1A)(d)", "Incendiary ammunition."),
            ("5(1A)(e)", "Armour-piercing ammunition."),
            ("5(1A)(f)", "Expanding ammunition for use with pistols and revolvers."),
            ("5(1A)(g)", "Expanding, explosive, armour-piercing or incendiary projectiles."),
        )

        Section5Clause.objects.bulk_create(
            [
                Section5Clause(clause=clause, description=description, created_by=ilb_admin_user)
                for clause, description in dummy_section_5_clauses
            ]
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if settings.APP_ENV in ["hotfix", "production"]:
            raise CommandError("Can only add dummy data in non-production environments.")

        # Create groups and load the groups we want to assign to test users:
        call_command("create_icms_groups")
        nca_case_officer = Group.objects.get(name="NCA Case Officer")
        ho_case_officer = Group.objects.get(name="Home Office Case Officer")
        san_case_officer = Group.objects.get(name="Sanctions Case Officer")
        import_search_user = Group.objects.get(name="Import Search User")
        dev_admin_group = Group.objects.get(name="Dev Admin")

        # Load application test data
        load_app_test_data()

        # Enable disabled application types to test / develop them
        if settings.SET_INACTIVE_APP_TYPES_ACTIVE:
            ImportApplicationType.objects.update(is_active=True)
            ExportApplicationType.objects.update(is_active=True)

        self.add_ilb_admin_users(options["password"])
        self.add_importers_and_users(options["password"])
        self.add_exporters_and_users(options["password"])

        self.create_user(
            username="nca_admin",
            password=options["password"],
            first_name="Clara",
            last_name="Boone",
            groups=[nca_case_officer],
        )
        self.create_user(
            username="nca_admin_2",
            password=options["password"],
            first_name="Kara",
            last_name="Moses",
            groups=[nca_case_officer],
        )

        self.create_user(
            username="ho_admin",
            password=options["password"],
            first_name="Steven",
            last_name="Hall",
            groups=[ho_case_officer],
        )

        self.create_user(
            username="ho_admin_2",
            password=options["password"],
            first_name="Dawn",
            last_name="Cabrera",
            groups=[ho_case_officer],
        )

        self.create_user(
            username="san_admin",
            password=options["password"],
            first_name="Karen",
            last_name="Bradley",
            groups=[san_case_officer],
        )

        self.create_user(
            username="san_admin_2",
            password=options["password"],
            first_name="Emilio",
            last_name="Mcgee",
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
            username="con_user_2",
            password=options["password"],
            first_name="Patrick",
            last_name="Ashley",
            linked_constabularies=Constabulary.objects.filter(
                name__in=["Lancashire", "Merseyside"]
            ),
        )

        self.create_user(
            username="import_search_user",
            password=options["password"],
            first_name="Hercule",
            last_name="Poirot",
            groups=[import_search_user],
        )

        self.create_user(
            username="import_search_user_2",
            password=options["password"],
            first_name="Safiyyah",
            last_name="Thomson",
            groups=[import_search_user],
        )

        self.create_user(
            username="dev_admin",
            password=options["password"],
            first_name="Maurice",
            last_name="Moss",
            groups=[dev_admin_group],
        )

        self.create_superuser("admin", options["password"])

        self.stdout.write(
            f"Created following users: {', '.join([repr(u) for u in self.users_created])}"
        )
        self.stdout.write("Created following superusers: 'admin'")

        # Add a dummy biocidal_claim legislation (defaults to GB and NI legislation)
        ProductLegislation.objects.create(
            name="Dummy 'Is Biocidal Claim legislation'", is_biocidal_claim=True
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
        is_pesticide_on_free_sale_uk=False,
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
        template_country=CertificateApplicationTemplate.CountryType.GB,
        sharing=CertificateApplicationTemplate.SharingStatuses.EDIT,
        owner=owner,
    )
    cfs_template = CertificateOfFreeSaleApplicationTemplate.objects.create(template=cfs_cat)
    cfs_schedule_template = CFSScheduleTemplate.objects.create(
        application=cfs_template,
        created_by=owner,
        exporter_status=CFSScheduleTemplate.ExporterStatus.IS_MANUFACTURER,
        brand_name_holder=YesNoChoices.yes,
    )

    # Add a biocidal product legislation as we add product types and active ingredients later on.
    cfs_schedule_template.legislations.add(
        ProductLegislation.objects.filter(is_biocidal=True).first()
    )

    # Sample of valid cas numbers to add
    valid_cas_numbers = [
        "12002-61-8",
        "7440-22-4",
        "27039-77-6",
        "7785-23-1",
        "7783-89-3",
        "506-64-9",
        "563-63-3",
        "7783-90-6",
    ]

    for i in range(1, 6):
        product = cfs_schedule_template.products.create(product_name=f"Test Product {i}")
        for z in range(1, i + 1):
            product.product_type_numbers.create(product_type_number=z)
            z = str(z)  # type:ignore[assignment]
            cas = valid_cas_numbers[i - 1]
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
    file_path = settings.BASE_DIR / "web/static/web/img/dit-no-signature.jpg"

    if not file_path.is_file():
        raise CommandError("Dummy signature file missing")

    filename = "active_dummy_signature.jpg"
    key = f"dummy_signature/{filename}"
    file_size = upload_file_obj_to_s3(file_path.open("rb"), key)

    Signature.objects.create(
        name="Active Dummy Signature",
        signatory="Import Licencing Branch",
        history=f"Created by add_dummy_data command on {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        filename=filename,
        path=key,
        content_type="image/jpg",
        created_by=user,
        file_size=file_size,
        is_active=True,
    )


def create_dummy_file(model: models.Model, user: User) -> File:
    file_path = settings.BASE_DIR / "dummy-file.txt"
    with file_path.open("w") as file:
        file.write("sometext\n")

    # model id - timestamp - filename
    time_stamp = f'{timezone.now().strftime("%Y%m%d%H%M%S")}'
    key = f"{model.pk}_{time_stamp}_{file_path.name}"

    file_size = upload_file_obj_to_s3(file_path.open("rb"), key)

    file = File.objects.create(
        is_active=True,
        filename=file_path.name,
        content_type=file_path.suffix,
        file_size=file_size,
        path=key,
        created_by=user,
    )
    file_path.unlink()

    return file
