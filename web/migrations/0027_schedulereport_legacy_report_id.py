# Generated by Django 4.2.14 on 2024-07-23 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0026_reports"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedulereport",
            name="legacy_report_id",
            field=models.IntegerField(null=True),
        ),
    ]
