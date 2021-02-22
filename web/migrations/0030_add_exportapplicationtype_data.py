from django.db import migrations


def add_export_data(apps, schema_editor):
    ExportApplicationType = apps.get_model("web", "ExportApplicationType")
    CountryGroup = apps.get_model("web", "CountryGroup")

    cfs_cg = CountryGroup.objects.get(name="Certificate of Free Sale Countries")

    cfg_cg_for_com = CountryGroup.objects.get(
        name="Certificate of Free Sale Country of Manufacture Countries"
    )

    com_cg = CountryGroup.objects.get(name="Certificate of Manufacture Countries")

    ExportApplicationType.objects.create(
        type_code="CFS",
        type="Certificate of Free Sale",
        allow_multiple_products=True,
        generate_cover_letter=False,
        allow_hse_authorization=False,
        country_group=cfs_cg,
        country_group_for_manufacture=cfg_cg_for_com,
    )

    ExportApplicationType.objects.create(
        type_code="COM",
        type="Certificate of Manufacture",
        allow_multiple_products=False,
        generate_cover_letter=False,
        allow_hse_authorization=False,
        country_group=com_cg,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0029_add_country_group_data"),
    ]

    operations = [
        migrations.RunPython(add_export_data),
    ]
