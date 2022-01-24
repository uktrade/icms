import pathlib
import textwrap

from django.db import migrations

from web.management.commands.countries import read_country_csv

# Data spreadsheet, in the web/migrations directory.
CSV_FILENAME = "countries-groups.csv"


def load_country_group_data(apps, schema_editor):
    CountryGroup = apps.get_model("web", "CountryGroup")
    Country = apps.get_model("web", "Country")

    filename = pathlib.Path(__file__).parent / CSV_FILENAME

    with open(filename) as fh:
        country_data, group_data = read_country_csv(fh)

    # First we bulk create the groups themselves (without membership).
    groups = []

    for row in group_data:
        group = CountryGroup(name=row["name"], comments=row["comments"])
        groups.append(group)

    CountryGroup.objects.bulk_create(groups)

    # Now we can find the Country database objects and populate the groups.
    groups_map = {g.name: g for g in CountryGroup.objects.all()}
    countries_map = {c.name: c for c in Country.objects.all()}
    # We will build a map with the key being a group name, and the value a list
    # of Country objects.
    membership = {g: [] for g in groups_map}

    for row in country_data:
        country = countries_map[row["name"]]

        for gname in row["groups"]:
            membership[gname].append(country)

    for gname, countries in membership.items():
        group = groups_map[gname]
        group.countries.add(*countries)


class Migration(migrations.Migration):
    dependencies = [
        ("web", "0002_add_country_data"),
    ]

    operations = [
        migrations.RunPython(load_country_group_data),
    ]
