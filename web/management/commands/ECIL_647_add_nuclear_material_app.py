from django.core.management.base import BaseCommand

from web.models import ImportApplicationType, Template, Unit


# To run: make manage args="ECIL_647_add_nuclear_material_app"
class Command(BaseCommand):
    help = """Add data for nuclear material application. Currently this cannot be done
    via django migrations due to the test data using fixtures that a populated only once the migrations have run"""

    def handle(self, *args, **options):
        self.fix_all_quantity_codes()

        if ImportApplicationType.objects.filter(type="NMIL").exists():
            self.stdout.write(
                "Nuclear Materials Import Licence Application already exists in data. Exiting command."
            )
            return
        gen_dec = Template.objects.get(template_code=Template.Codes.IMA_GEN_DECLARATION)

        ImportApplicationType.objects.create(
            # Fields used by ICMS
            is_active=False,
            type=ImportApplicationType.Types.NMIL,
            sub_type=None,
            name="Nuclear Materials Import Licence Application",
            sigl_flag=False,
            chief_flag=True,
            paper_licence_flag=False,
            electronic_licence_flag=True,
            cover_letter_flag=False,
            declaration_template=gen_dec,
            # Fields not used in ICMS but need a value to save record
            licence_type_code=ImportApplicationType.Types.NMIL,
            chief_licence_prefix="GBSIL",
            cover_letter_schedule_flag=False,
            category_flag=True,
            quantity_unlimited_flag=False,
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=True,
            multiple_commodities_flag=True,
            usage_auto_category_desc_flag=False,
            case_checklist_flag=True,
            importer_printable=False,
        )
        self.stdout.write("Nuclear Materials Import Licence Application created.")

    def fix_all_quantity_codes(self):
        """Add all CDS supported units

        # All available quantity codes:
        # https://www.gov.uk/government/publications/uk-trade-tariff-quantity-codes/uk-trade-tariff-quantity-codes
        """

        self.stdout.write("Adding units.")

        # Units in the production that won't be touched (as they aren't valid records):
        # "pieces" - "30" (code 30 should have label "number")
        # "units" - "30" (code 30 should have label "number")
        # "Barrels" - "30" (code 30 should have label "number")
        # "euro CIF" - "30" (code 30 should have label "number")

        # Unit's in production to fix:
        # "kilos" - "23" (label only)
        u = Unit.objects.get(description="kilos")
        u.description = "Kilogramme"
        u.save()
        # "metric carats" - "30" (label and hmrc_code)
        u = Unit.objects.get(description="metric carats")
        u.description = "Metric Carat"
        u.hmrc_code = "26"
        u.save()
        # "pairs" - "31" (label only)
        u = Unit.objects.get(description="pairs")
        u.description = "Pair"
        u.save()
        # "sq.metres" - "45" (label only)
        u = Unit.objects.get(description="sq.metres")
        u.description = "Square metre"
        u.save()
        # "cubic metres" - "87" (label only)
        u = Unit.objects.get(description="cubic metres")
        u.description = "Cubic metre"
        u.save()

        # Now all the existing records have been changed do the following:
        #   1. Create all other values
        #   2. Set a common unit_type for each section
        #   3. set short_description to "N/a" as it isn't used

        #  1. Weight
        weights = [
            ("Ounce", "11"),
            ("Pound", "12"),
            ("Cental (100lb)", "13"),
            ("Cwt", "14"),
            ("1,000lb", "15"),
            ("Ton", "16"),
            ("Oz Troy", "17"),
            ("Lb Troy", "18"),
            ("Gramme", "21"),
            ("Hectogramme (100 gms)", "22"),
            ("Kilogramme", "23"),
            ("100 kgs", "24"),
            ("Tonne", "25"),
            ("Metric Carat", "26"),
            ("50 kgs", "27"),
        ]
        for description, code in weights:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Weight"
            unit.short_description = "N/a"
            unit.save()

        # 2. Gross weight
        gross_weights = [
            ("Pound gross", "60"),
            ("Kilogramme gross", "61"),
            ("Quintal (100 kgs) gross", "62"),
        ]
        for description, code in gross_weights:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Gross weight"
            unit.short_description = "N/a"
            unit.save()

        # 3. Unit
        units = [
            ("Number", "30"),
            ("Pair", "31"),
            ("Dozen", "32"),
            ("Dozen Pair", "33"),
            ("Hundred", "34"),
            ("Long Hundred", "35"),
            ("Gross", "36"),
            ("Thousand", "37"),
            ("Short Standard", "38"),
        ]
        for description, code in units:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Unit"
            unit.short_description = "N/a"
            unit.save()

        # 4. Area
        areas = [
            ("Square inch", "41"),
            ("Square foot", "42"),
            ("Square yard", "43"),
            ("Square decimetre", "44"),
            ("Square metre", "45"),
            ("100 square metres", "46"),
        ]
        for description, code in areas:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Area"
            unit.short_description = "N/a"
            unit.save()

        # 5. Length
        lengths = [
            ("Inch", "50"),
            ("Foot", "51"),
            ("Yard", "52"),
            ("100 feet", "53"),
            ("Millimetre", "54"),
            ("Centimetre", "55"),
            ("Decimetre", "56"),
            ("Metre", "57"),
            ("Dekametre", "58"),
            ("Hectometre", "59"),
        ]
        for description, code in lengths:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Length"
            unit.short_description = "N/a"
            unit.save()

        # 6. Capacity
        capacities = [
            ("Pint", "71"),
            ("Gallon", "72"),
            ("36 gallons (Bulk barrel)", "73"),
            ("Millilitre (cu centimetre)", "74"),
            ("Centilitre", "75"),
            ("Litre", "76"),
            ("Dekalitre", "77"),
            ("Hectolitre", "78"),
            ("US Gallon", "79"),
            ("1000 litre", "40"),
        ]
        for description, code in capacities:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Capacity"
            unit.short_description = "N/a"
            unit.save()

        # 7. Volume
        volumes = [
            ("Cubic inch", "81"),
            ("Cubic foot", "82"),
            ("Cubic yard", "83"),
            ("Standard", "84"),
            ("Piled cubic fathom", "85"),
            ("Cubic decimetre", "86"),
            ("Cubic metre", "87"),
            ("Piled cubic metre", "88"),
            ("Gram fissile isotopes", "89"),
        ]
        for description, code in volumes:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Volume"
            unit.short_description = "N/a"
            unit.save()

        # 8. Various
        various = [
            ("Kilogramme of H2O2", "29"),
            ("Kilogramme of K2O", "01"),
            ("Kilogramme of KOH", "02"),
            ("Kilogramme of N", "03"),
            ("Kilogramme of NaOH", "04"),
            ("Kilogramme of P2O5", "05"),
            ("Kilogramme of U", "06"),
            ("Kilogramme of WO3", "07"),
            ("Number of flasks", "08"),
            ("Number of kits", "09"),
            ("Number of rolls", "10"),
            ("Number of sets", "19"),
            ("100 packs", "20"),
            ("1000 tablets", "28"),
            ("100 kilogram net dry matter", "48"),
            ("100 kilogram drained net weight", "49"),
            ("Kilogram of choline chloride", "107"),
            ("Kilogram of methyl amines", "39"),
            ("Kilogramme of total alcohol", "63"),
            ("CCT carrying capacity in Tonnes (metric) shipping", "64"),
            ("Gram (fine gold content)", "65"),
            ("Litre of alcohol", "66"),
            ("Litre of alcohol in the spirit", "66"),
            ("Litre of pure 100% alcohol", "66"),
            ("Kilogramme 90% dry", "67"),
            ("90% tonne dry", "68"),
            ("Kilogramme drained net weight", "69"),
            ("Standard litre (of hydrocarbon oil)", "70"),
            ("1000 cubic metres", "80"),
            ("Curie", "90"),
            ("Proof gallon", "91"),
            ("Displacement tonnage", "92"),
            ("Gross tonnage", "93"),
            ("100 international units", "94"),
            ("Million international units potency", "95"),
            ("Kilowatt", "96"),
            ("Kilowatt hour", "97"),
            ("Alcohol by Volume (ABV%) Beer", "98"),
            ("Degrees (Percentage Volume)", "99"),
            ("TJ (gross calorific value)", "120"),
            ("Euro per tonne of fuel", "112"),
            ("Euro per tonne net of biodiesel content", "113"),
            ("Kilometres", "114"),
            ("Euro per tonne net of bioethanol content", "115"),
            ("Number of watt", "117"),
            ("Kilogram Raw Sugar", "118"),
            ("KAC: (KG net of Acesulfame Potassium)", "119"),
        ]
        for description, code in various:
            unit, _ = Unit.objects.get_or_create(description=description, hmrc_code=code)
            unit.unit_type = "Various"
            unit.short_description = "N/a"
            unit.save()
