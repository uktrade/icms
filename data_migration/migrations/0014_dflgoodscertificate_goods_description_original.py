# Generated by Django 4.2.16 on 2024-09-17 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_migration", "0013_sil_application_goods_overrides"),
    ]

    operations = [
        migrations.AddField(
            model_name="dflgoodscertificate",
            name="goods_description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
    ]
