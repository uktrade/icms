from django.core.management.color import no_style
from django.db import migrations, transaction, connection
from web.models import Country
from django.conf import settings
import os
import json


def reset_country_sequence(apps, schema_editor):
    sequence_reset_sql = connection.ops.sequence_reset_sql(
        no_style(), [
            Country,
        ])
    with connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


def save_countries(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/countries.json')) as f:
        countries = json.load(f)
        with transaction.atomic():
            for const in countries:
                # Make json keys lowercase
                country_lower = {}
                for key, value in const.items():
                    country_lower[key.lower()] = value
                Country(**country_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0022_auto_20190624_0944'),
    ]

    operations = [
        migrations.RunPython(save_countries),
        migrations.RunPython(reset_country_sequence)
    ]
