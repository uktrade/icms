
from django.core.management.color import no_style
from django.db import migrations, transaction, connection
from web.models import CountryGroup
from django.conf import settings
import os
import json


def reset_country_group_sequence(apps, schema_editor):
    sequence_reset_sql = connection.ops.sequence_reset_sql(
        no_style(), [
            CountryGroup,
        ])
    with connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


def save_country_groups(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/country-groups.json')) as f:
        groups = json.load(f)
        with transaction.atomic():
            for group in groups:
                # Make json keys lowercase
                group_lower = {}
                countries = []
                for key, value in group.items():
                    if key == 'COUNTRIES':
                        countries = value.split(',')
                        continue
                    group_lower[key.lower()] = value
                country_group = CountryGroup(**group_lower)
                country_group.save()
                country_group.countries.set(countries)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0024_auto_20190624_1100'),
    ]

    operations = [
        migrations.RunPython(save_country_groups),
        migrations.RunPython(reset_country_group_sequence)
    ]
