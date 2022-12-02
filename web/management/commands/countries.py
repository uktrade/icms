import argparse
import csv
import operator
import sys
from collections.abc import Iterable
from typing import Any, TextIO

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from web.domains.country.models import Country, CountryGroup

# The column / field order is also used to check we have a valid-looking input
# when reading a CSV and loading data.
COUNTRY_FIELDS = ["id", "name", "is_active", "type", "commission_code", "hmrc_code"]
# Marker in a spreadsheet cell to indicate group membership.
MEMBERSHIP = "Y"


class Command(BaseCommand):
    help = "Import countries data from <stdin> or export to <stdout>"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "operation", choices=["import", "export"], help="Import or export countries data"
        )

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

    # Country group comments immediately below the column headers.
    row = {group.name: group.comments for group in groups}
    writer.writerow(row)

    for country in countries:
        row = dict(zip(COUNTRY_FIELDS, getter(country)))
        # Add a mark for each group this country belongs to.
        row.update({group.name: MEMBERSHIP for group in country.country_groups.all()})
        writer.writerow(row)


def read_country_csv(src: TextIO = sys.stdin) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    reader = csv.reader(src)
    header_start_len = len(COUNTRY_FIELDS)

    groups = []
    groupnames = []
    countries = []

    # Ignore any rows at the beginning until we find a valid header. N.B. CSV
    # reader returns rows as list (not tuple).
    for row in reader:
        if row[:header_start_len] == COUNTRY_FIELDS:
            # Nice. We found the header row. The country group names are the
            # remaining column values in this row. Following row is comments for
            # the groups, after which we get the countries and membership.
            groupnames = row[header_start_len:]
            try:
                comments = next(reader)[header_start_len:]
            except StopIteration:
                # No more rows! But we need empty comments for the zip below.
                comments = [""] * len(groupnames)

            for name, comment in zip(groupnames, comments):
                groups.append({"name": name, "comments": comment})

            break
    else:
        # We went through every row, no header found.
        raise ValueError(f"Missing header, expected columns {COUNTRY_FIELDS}")

    # Remaining rows are country data.
    for row in reader:
        country: dict[str, Any] = dict(zip(COUNTRY_FIELDS, row[:header_start_len]))
        member = dict(zip(groupnames, row[header_start_len:]))
        country["groups"] = [k for k, v in member.items() if v == MEMBERSHIP]

        countries.append(country)

    return countries, groups
