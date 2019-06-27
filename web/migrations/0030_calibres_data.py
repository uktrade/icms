from django.core.management.color import no_style
from django.db import migrations, transaction, connection
from web.models import ObsoleteCalibreGroup, ObsoleteCalibre
from django.conf import settings
import os
import json


def reset_calibre_sequences(apps, schema_editor):
    sequence_reset_sql = connection.ops.sequence_reset_sql(
        no_style(), [
            ObsoleteCalibreGroup,
            ObsoleteCalibre
        ])
    with connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


def save_calibre_groups(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/calibre-groups.json')) as f:
        calibre_group = json.load(f)
        for group in calibre_group:
            # Make json keys lowercase
            group_lower = {}
            for key, value in group.items():
                group_lower[key.lower()] = value
            ObsoleteCalibreGroup(**group_lower).save()


def save_calibres(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/obsolete-calibres.json')) as f:
        calibres = json.load(f)
        for calibre in calibres:
            # Make json keys lowercase
            calibre_lower = {}
            for key, value in calibre.items():
                calibre_lower[key.lower()] = value
            ObsoleteCalibre(**calibre_lower).save()


def save_calibres_data(apps, schema_editor):
    with transaction.atomic():
        save_calibre_groups(apps, schema_editor)
        save_calibres(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0029_obsoletecalibre_obsoletecalibregroup'),
    ]

    operations = [
        migrations.RunPython(save_calibres_data),
        migrations.RunPython(reset_calibre_sequences)
    ]
