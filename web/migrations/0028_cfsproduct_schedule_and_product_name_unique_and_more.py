# Generated by Django 4.2.14 on 2024-08-14 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0027_schedulereport_legacy_report_id"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="cfsproduct",
            constraint=models.UniqueConstraint(
                fields=("schedule", "product_name"), name="schedule_and_product_name_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="cfsproductactiveingredient",
            constraint=models.UniqueConstraint(
                fields=("product", "cas_number"), name="product_and_cas_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="cfsproductactiveingredient",
            constraint=models.UniqueConstraint(
                fields=("product", "name"), name="product_and_name_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="cfsproducttype",
            constraint=models.UniqueConstraint(
                fields=("product", "product_type_number"), name="product_and_ptn_unique"
            ),
        ),
    ]