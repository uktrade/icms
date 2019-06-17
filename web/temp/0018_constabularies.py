from django.db import migrations, transaction
from web.models import Constabulary
from django.conf import settings
import os
import json


def save_constabularies(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/constabularies.json')) as f:
        constabularies = json.load(f)
        with transaction.atomic():
            for const in constabularies:
                # Make json keys lowercase
                const_lower = {}
                for key, value in const.items():
                    const_lower[key.lower()] = value
                Constabulary(**const_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0017_auto_20190604_1644'),
    ]

    operations = [migrations.RunPython(save_constabularies)]
