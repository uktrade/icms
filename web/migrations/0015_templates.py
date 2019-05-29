from django.db import migrations, transaction
from django.utils.timezone import make_aware
from datetime import datetime
from web.models import Template
from django.conf import settings
import os
import json


def save_templates(apps, schema_editor):
    with open(os.path.join(settings.BASE_DIR,
                           'reference-data/template.json')) as f:
        templates = json.load(f)
        for template in templates:
            with transaction.atomic():
                # Make keys lowercase
                template_lower = {}
                for key, value in template.items():
                    val = value
                    if key in ('START_DATETIME', 'END_DATETIME') and val:
                        val = make_aware(
                            datetime.strptime(val, '%d-%b-%Y %H:%M:%S'))
                    template_lower[key.lower()] = val
                Template(**template_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0014_auto_20190529_1454'),
    ]

    operations = [migrations.RunPython(save_templates)]
