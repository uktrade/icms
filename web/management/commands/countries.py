import csv
import operator
import sys
from typing import Any, Iterable, TextIO

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from web.domains.country.models import Country, CountryGroup

# The column / field order is also used to check we have a valid-looking input
# when reading a CSV and loading data.
COUNTRY_FIELDS = ["id", "name", "is_active", "type", "commission_code", "hmrc_code"]
# Marker in a spreadsheet cell to indicate group membership.
MEMBERSHIP = "Y"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("operation", choices=["import", "export"])

    def handle(self, *args, **options):
        if options["operation"] == "export":
            countries, groups = get_country_data()
            write_country_csv(countries, groups, dest=self.stdout)
            self.stderr.write(f"Wrote CSV data to {self.stdout}")
        elif options["operation"] == "import":
            self.stderr.write(f"Reading CSV data from {sys.stdin}")
            countries, groups = read_country_csv(src=sys.stdin)
            self.stderr.write(f"Summary: {len(groups)} groups, {len(countries)} countries.")
            self.stderr.write("No data was imported (not implemented).")


def get_country_data() -> tuple[QuerySet[Country], QuerySet[CountryGroup]]:
    countries = Country.objects.prefetch_related("country_groups").all()
    groups = CountryGroup.objects.all()

    return countries, groups


def write_country_csv(
    countries: Iterable[Country], groups: Iterable[CountryGroup], dest: TextIO = sys.stdout
):
    getter = operator.attrgetter(*COUNTRY_FIELDS)
    groupnames = sorted(g.name for g in groups)
    # First few column names are country fields, followed by a column for
    # each of the named groups (there are more than a dozen groups).
    fieldnames = COUNTRY_FIELDS + groupnames

    writer = csv.DictWriter(dest, fieldnames)
    writer.writeheader()

    for country in countries:
        row = dict(zip(COUNTRY_FIELDS, getter(country)))
        # Add a mark for each group this country belongs to.
        row.update({group.name: MEMBERSHIP for group in country.country_groups.all()})
        writer.writerow(row)


def read_country_csv(src: TextIO = sys.stdin) -> tuple[list[dict[str, Any]], list[str]]:
    reader = csv.reader(src)
    header_start_len = len(COUNTRY_FIELDS)

    groupnames = []
    countries = []

    # Ignore any rows at the beginning until we find a valid header. N.B. CSV
    # reader returns rows as list (not tuple).
    for row in reader:
        if row[:header_start_len] == COUNTRY_FIELDS:
            # Nice. We found the header row. The country group names are the
            # remaining column values in this row. Then the actual country
            # data starts on the next row.
            groupnames = row[header_start_len:]
            break
    else:
        # We went through every row, no header found.
        raise ValueError(f"Missing header, expected columns {COUNTRY_FIELDS}")

    # Remaining rows are country data.
    for row in reader:
        country: dict[str, Any] = dict(zip(COUNTRY_FIELDS, row[:header_start_len]))
        groups = dict(zip(groupnames, row[header_start_len:]))
        country["groups"] = [k for k, v in groups.items() if v == MEMBERSHIP]

        countries.append(country)

    return countries, groupnames
