# Generated by Django 4.2.16 on 2024-09-17 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_migration", "0012_importapplicationlicence_issue_datetime"),
    ]

    operations = [
        migrations.AddField(
            model_name="dflapplication",
            name="commodities_response_xml",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="openindividuallicenceapplication",
            name="commodities_response_xml",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="silapplication",
            name="commodities_response_xml",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection1",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection1",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection2",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection2",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection5",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection5",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection582obsolete",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection582obsolete",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection582other",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="silgoodssection582other",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name="sillegacygoods",
            name="description_original",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name="sillegacygoods",
            name="quantity_original",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection1",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection2",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection5",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection582obsolete",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection582obsolete",
            name="quantity",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection582other",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="silgoodssection582other",
            name="quantity",
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="sillegacygoods",
            name="description",
            field=models.CharField(max_length=4096, null=True),
        ),
    ]