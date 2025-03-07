from django.core.management.base import BaseCommand

from web.models import ImportApplicationType, Template, Unit


class Command(BaseCommand):
    help = """Add data for nuclear material application. Currently this cannot be done
    via django migrations due to the test data using fixtures that a populated only once the migrations have run"""

    def handle(self, *args, **options):
        if ImportApplicationType.objects.filter(type="NMIL").exists():
            self.stdout.write(
                "Nuclear Materials Import Licence Application already exists in data. Exiting command."
            )
            return

        self.add_units()
        gen_dec = Template.objects.get(template_code=Template.Codes.IMA_GEN_DECLARATION)

        ImportApplicationType.objects.create(
            is_active=False,
            type="NMIL",
            sub_type="NMIL",
            name="Nuclear Materials Import Licence Application",
            licence_type_code="ADHOC",  # TODO: Check this value is correct
            sigl_flag=False,
            chief_flag=True,
            chief_licence_prefix="GBSAN",  # TODO: Confirm with HMRC the licence prefix
            paper_licence_flag=False,
            electronic_licence_flag=True,
            cover_letter_flag=False,
            cover_letter_schedule_flag=False,
            category_flag=True,
            quantity_unlimited_flag=False,
            unit_list_csv="KGS,G,MCG,ML,L",
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=True,
            multiple_commodities_flag=True,
            guidance_file_url="/docs/ApplyingForSanctionsLicence.pdf",  # TODO: Update to actual value
            usage_auto_category_desc_flag=False,
            case_checklist_flag=True,
            importer_printable=False,
            declaration_template=gen_dec,
        )
        self.stdout.write("Nuclear Materials Import Licence Application created.")

    def add_units(self):

        self.stdout.write("Adding units.")
        units = [
            {"unit_type": "G", "description": "grams", "short_description": "g", "hmrc_code": 21},
            {
                "unit_type": "MCG",
                "description": "micrograms",
                "short_description": "mcg",
                "hmrc_code": 21,  # TODO check if there is a hmrc code for mcg
            },
            {
                "unit_type": "ML",
                "description": "millilitres",
                "short_description": "ml",
                "hmrc_code": 74,
            },
            {"unit_type": "L", "description": "litres", "short_description": "l", "hmrc_code": 76},
        ]

        for unit in units:
            Unit.objects.get_or_create(**unit)
