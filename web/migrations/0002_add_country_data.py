import pathlib

from django.db import migrations

from web.management.commands.countries import read_country_csv

# Data spreadsheet, in the web/migrations directory.
CSV_FILENAME = "countries-groups.csv"


def load_country_data(apps, schema_editor):
    Country = apps.get_model("web", "Country")
    filename = pathlib.Path(__file__).parent / CSV_FILENAME

    with open(filename) as fh:
        country_data, _ = read_country_csv(fh)

    countries = []

    for row in country_data:
        country = Country(
            name=row["name"],
            is_active=(row["is_active"].upper() == "TRUE"),
            type=row["type"],
            commission_code=row["commission_code"],
            hmrc_code=row["hmrc_code"],
        )
        countries.append(country)

    Country.objects.bulk_create(countries)


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_country_data),
    ]
