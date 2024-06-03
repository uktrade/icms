# Generated by Django 4.2.13 on 2024-05-30 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0010_exporter_exclusive_correspondence"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cfsproductactiveingredient",
            name="cas_number",
            field=models.CharField(
                help_text="A CAS (Chemical Abstracts Service) Registry Number is a unique chemical identifier. Numbers must be separated by hyphens. For example, the CAS number for caffeine is 58-08-2.",
                max_length=50,
                verbose_name="CAS Number",
            ),
        ),
        migrations.AlterField(
            model_name="cfsproductactiveingredienttemplate",
            name="cas_number",
            field=models.CharField(
                help_text="A CAS (Chemical Abstracts Service) Registry Number is a unique chemical identifier. Numbers must be separated by hyphens. For example, the CAS number for caffeine is 58-08-2.",
                max_length=50,
                verbose_name="CAS Number",
            ),
        ),
    ]