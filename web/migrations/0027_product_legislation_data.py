from django.core.management.color import no_style
from django.db import migrations, transaction, connection
from web.models import ProductLegislation
from django.conf import settings
import os
import json


def reset_product_legislation_sequence(apps, schema_editor):
    sequence_reset_sql = connection.ops.sequence_reset_sql(
        no_style(), [
            ProductLegislation,
        ])
    with connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


def save_product_legislation(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/product-legislation.json')) as f:
        product_legislation = json.load(f)
        with transaction.atomic():
            for legislation in product_legislation:
                # Make json keys lowercase
                legislation_lower = {}
                for key, value in legislation.items():
                    legislation_lower[key.lower()] = value
                ProductLegislation(**legislation_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0026_auto_20190625_1354'),
    ]

    operations = [
        migrations.RunPython(save_product_legislation),
        migrations.RunPython(reset_product_legislation_sequence)
    ]
