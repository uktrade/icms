# Generated by Django 4.2.16 on 2024-11-12 13:15

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0048_user_email_verification"),
    ]

    operations = [
        migrations.AddField(
            model_name="file",
            name="clam_av_results",
            field=models.JSONField(
                encoder=django.core.serializers.json.DjangoJSONEncoder, null=True
            ),
        ),
    ]