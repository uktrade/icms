from django.core import management
from django.core.management.commands import loaddata
from django.db import migrations, transaction
from django.utils.timezone import make_aware
from datetime import datetime
from web.models import CommodityGroup, Unit
from django.conf import settings
import os
import json


def load_units(apps, schema_editor):
    management.call_command(loaddata.Command(), 'web/fixtures/web/units.json')


def save_commodity_groups(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/commodity-groups.json')) as f:
        groups = json.load(f)
        with transaction.atomic():
            for group in groups:
                # Make keys lowercase
                group_lower = {}
                commodities = []
                for key, value in group.items():
                    val = value
                    if val:
                        if key in ('START_DATETIME', 'END_DATETIME'):
                            val = make_aware(
                                datetime.strptime(val, '%d-%b-%Y %H:%M:%S'))
                        elif key == 'UNIT':
                            val = Unit.objects.get(unit_type=val)
                        elif key == 'COMMODITIES':
                            commodities = val.split(',')
                            continue
                    elif key == 'COMMODITIES':
                        continue
                    group_lower[key.lower()] = val
                com_group = CommodityGroup(**group_lower)
                if (commodities):
                    com_group.commodities.set(commodities)
                com_group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0019_commodity_data'),
    ]

    operations = [
        migrations.RunPython(load_units),
        migrations.RunPython(save_commodity_groups)
    ]
