# Generated by Django 4.2.13 on 2024-05-21 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_migration", "0007_rename_section_5_clause_silgoodssection5_section_5_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="exporter",
            name="exclusive_correspondence",
            field=models.BooleanField(default=False),
        ),
    ]
