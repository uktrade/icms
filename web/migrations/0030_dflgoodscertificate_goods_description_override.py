# Generated by Django 4.2.14 on 2024-08-15 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0029_sanctionsandadhocapplicationgoods_goods_overrides"),
    ]

    operations = [
        migrations.AddField(
            model_name="dflgoodscertificate",
            name="goods_description_override",
            field=models.CharField(max_length=4096, null=True, verbose_name="Goods Description"),
        ),
    ]
