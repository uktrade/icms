# Generated by Django 4.2.13 on 2024-07-15 15:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_migration", "0009_alter_dflsupplementaryreport_created_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="caseemail",
            name="closed_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="data_migration.user",
            ),
        ),
        migrations.AddField(
            model_name="caseemail",
            name="email_type",
            field=models.CharField(max_length=30),
        ),
        migrations.AddField(
            model_name="caseemail",
            name="sent_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="data_migration.user",
            ),
        ),
    ]
