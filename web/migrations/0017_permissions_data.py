from django.core.management.color import no_style
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import migrations, transaction, connection
import os
import json


def reset_permission_sequence(apps, schema_editor):
    sequence_reset_sql = connection.ops.sequence_reset_sql(
        no_style(), [
            Permission,
        ])
    with connection.cursor() as cursor:
        for sql in sequence_reset_sql:
            cursor.execute(sql)


def save_permissions(apps, schema_editor):
    with open(
            os.path.join(settings.BASE_DIR,
                         'reference-data/permissions.json')) as f:
        permissions = json.load(f)
        with transaction.atomic():
            for perm in permissions:
                # Make json keys lowercase
                perm_lower = {}
                for key, value in perm.items():
                    perm_lower[key.lower()] = value
                perm_lower['content_type'] = ContentType.objects.get_for_model(
                    Permission)
                Permission(**perm_lower).save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0016_auto_20190619_1055'),
    ]

    operations = [
        migrations.RunPython(save_permissions),
        migrations.RunPython(reset_permission_sequence)
    ]
