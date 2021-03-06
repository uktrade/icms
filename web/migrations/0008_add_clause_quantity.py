# Generated by Django 3.1.4 on 2020-12-14 15:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0007_section5authority_add_help_text"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClauseQuantity",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("quantity", models.IntegerField(blank=True, null=True)),
                ("infinity", models.BooleanField(default=False)),
                (
                    "section5authority",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="web.section5authority"
                    ),
                ),
                (
                    "section5clause",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="web.section5clause"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="section5authority",
            name="clauses",
            field=models.ManyToManyField(through="web.ClauseQuantity", to="web.Section5Clause"),
        ),
    ]
