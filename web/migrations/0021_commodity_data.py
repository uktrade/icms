from django.db import migrations, transaction
from django.utils.timezone import make_aware
from datetime import datetime
from web.models import Commodity
from django.conf import settings
import os
import json


def save_commodities(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/commodities.json')) as f:
        commodities = json.load(f)
        with transaction.atomic():
            for commodity in commodities:
                # Make keys lowercase
                commodity_lower = {}
                for key, value in commodity.items():
                    val = value
                    if val:
                        if key in ('START_DATETIME', 'END_DATETIME'):
                            val = make_aware(
                                datetime.strptime(val, '%d-%b-%Y %H:%M:%S'))
                        elif key in ('VALIDITY_START_DATE',
                                     'VALIDITY_END_DATE'):
                            val = datetime.strptime(val, '%d-%b-%Y')
                    commodity_lower[key.lower()] = val
                Commodity(**commodity_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0020_commodity'),
    ]

    operations = [migrations.RunPython(save_commodities)]
