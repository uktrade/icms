# Generated by Django 3.1.3 on 2020-11-25 14:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0003_approvalrequest_exporterapprovalrequest_importerapprovalrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="commodity",
            name="commodity_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="web.commoditytype",
            ),
        ),
        migrations.AlterField(
            model_name="commoditygroup",
            name="start_datetime",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="commoditytype",
            name="type",
            field=models.CharField(
                choices=[
                    ("Chemicals", "Chemicals"),
                    ("Firearms and Ammunition", "Firearms and Ammunition"),
                    ("Iron, Steel and Aluminium", "Iron, Steel and Aluminium"),
                    ("Oil and Petrochemicals", "Oil and Petrochemicals"),
                    ("Precious Metals and Stones", "Precious Metals and Stones"),
                    ("Textiles", "Textiles"),
                    ("Vehicles", "Vehicles"),
                    ("Wood", "Wood"),
                    ("Wood Charcoal", "Wood Charcoal"),
                ],
                max_length=50,
            ),
        ),
    ]
