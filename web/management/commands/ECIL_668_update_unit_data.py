import argparse
from dataclasses import dataclass

from django.core.management.base import BaseCommand

from web.models import Unit


@dataclass
class UnitData:
    name: str
    code: str
    new_name: str | None = None


UNIT_DATA = [
    UnitData("Kilogramme", "KGM", "Kilogram"),
    UnitData("Metric Carat", "CTM"),  # TODO check with HMRC
    UnitData("Pair", "NPR"),  # TODO check with HMRC
    UnitData("Square metre", "MTK"),
    UnitData("Cubic metre", "MTQ"),
    UnitData("CCT carrying capacity in Tonnes (metric) shipping", "CCT"),
    UnitData("euro CIF", "EUR"),
    UnitData("Gram fissile isotopes", "GFI"),  # Unit for NMIL?
    UnitData("Gramme", "GRM", "Gram"),
    UnitData("Gross tonnage", "GRT"),
    UnitData("Hectolitre", "HLT"),
    UnitData("Hectometre", "HMT"),
    UnitData("KAC: (KG net of Acesulfame Potassium)", "KAC"),
    UnitData("Kilogram of choline chloride", "KCC"),
    UnitData("Kilogramme of total alcohol", "KGM", "Kilogram of total alcohol"),
    UnitData("Kilogramme drained net weight", "KGM", "Kilogram drained net weight"),
    UnitData("Kilogramme gross", "KGM", "Kilogram gross"),
    UnitData("1000 litre", "KLT"),
    UnitData("Kilogramme of N", "KNI", "Kilogram of N"),
    UnitData("Kilogramme of H2O2", "KNS", "Kilogram of H2O2"),
    UnitData("Kilogramme of KOH", "KPH", "Kilogram of KOH"),
    UnitData("Kilogramme of K2O", "KPO", "Kilogram of K2O"),
    UnitData("Kilogramme of P2O5", "KPP", "Kilogram of P2O5"),
    UnitData("Kilogramme of NaOH", "KSH", "Kilogram of NaOH"),
    UnitData("Kilogramme of U", "KUR", "Kilogram of U"),  # Unit for NMIL?
    UnitData("Kilowatt hour", "KW1"),
    UnitData("Standard litre (of hydrocarbon oil)", "LHC"),
    UnitData("Litre of pure 100% alcohol", "LTR"),
    UnitData("Litre of alcohol", "LTR"),
    UnitData("Litre", "LTR"),
    UnitData("Millilitre (cu centimetre)", "MLT", "Millilitre"),
    UnitData("Square metre", "MTK"),
    UnitData("Cubic metre", "MTQ"),
    UnitData("Metre", "MTR"),
    UnitData("Tonne", "TNE"),
    UnitData("Number of watt", "WAT"),
]

NEW_UNITS = [
    UnitData("Microlitre", "MCL"),
    UnitData("Microgram", "MCG"),
    UnitData("Milligram", "MGM"),
]


class Command(BaseCommand):
    help = """Update data for units to add new HMRC codes for CDS. Currently this cannot be done
    via django migrations due to the test data using fixtures that a populated only once the migrations have run"""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--commit",
            action="store_true",
            default=False,
            help="Argument to commit changes to the database",
        )

    def handle(self, *args, **options):
        self.commit = options["commit"]
        self.update_unit_codes()
        self.add_new_units()

    def update_unit_codes(self):
        self.stdout.write("Updating exisitng units")
        for data in UNIT_DATA:
            try:
                unit = Unit.objects.get(description=data.name)
                unit.hmrc_unit_code = data.code

                if data.new_name:
                    unit.description = data.new_name
                    self.stdout.write(f"\t{data.name} -> {data.new_name} ({data.code})")
                else:
                    self.stdout.write(f"\t{data.name} ({data.code})")

                if self.commit:
                    self.stdout.write("\t\tCommitting")
                    unit.save()

            except Unit.DoesNotExist:
                self.stdout.write(f"\t{data.name} not found.")

    def add_new_units(self):
        self.stdout.write("")
        self.stdout.write("Creating new units")
        for data in NEW_UNITS:
            _, created = Unit.objects.get_or_create(description=data.name, hmrc_unit_code=data.code)
            if created:
                self.stdout.write(f"\t{data.name} ({data.code}) created")
            else:
                self.stdout.write(f"\t{data.name} ({data.code}) already exists")
