# Generated by Django 4.2.11 on 2024-08-02 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "web",
            "0023_alter_certificateofgoodmanufacturingpracticeapplication_manufacturer_address_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="exportapplication",
            name="decision",
            field=models.CharField(
                blank=True,
                choices=[("APPROVE", "Approve Application"), ("REFUSE", "Refuse Application")],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="importapplication",
            name="decision",
            field=models.CharField(
                blank=True,
                choices=[("APPROVE", "Approve Application"), ("REFUSE", "Refuse Application")],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="importapplication",
            name="variation_decision",
            field=models.CharField(
                choices=[("APPROVE", "Approve Application"), ("REFUSE", "Refuse Application")],
                max_length=10,
                null=True,
                verbose_name="Variation Decision",
            ),
        ),
    ]
