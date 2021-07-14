from django.db import migrations


def add_sanctions_and_adhoc_license_country_group(apps, schema_editor):
    Country = apps.get_model("web", "Country")
    CountryGroup = apps.get_model("web", "CountryGroup")
    group = CountryGroup.objects.create(name="Sanctions and Adhoc License")
    countries = ["Iran", "Korea (North)", "Russian Federation"]
    for country_name in countries:
        country = Country.objects.get(name=country_name)
        group.countries.add(country)
    group.save()


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0030_add_exportapplicationtype_data"),
    ]

    operations = [
        migrations.RunPython(add_sanctions_and_adhoc_license_country_group),
    ]
