# Generated by Django 5.1.4 on 2024-12-20 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0049_file_clam_av_results"),
    ]

    operations = [
        migrations.AlterField(
            model_name="countrygroup",
            name="name",
            field=models.CharField(
                choices=[
                    ("CFS", "Certificate of Free Sale Countries"),
                    ("CFS_COM", "Certificate of Free Sale Country of Manufacture Countries"),
                    ("COM", "Certificate of Manufacture Countries"),
                    ("GMP", "Goods Manufacturing Practice Countries"),
                    ("FA_DFL_IC", "Firearms and Ammunition (Deactivated) Issuing Countries"),
                    ("FA_OIL_COC", "Firearms and Ammunition (OIL) COCs"),
                    ("FA_OIL_COO", "Firearms and Ammunition (OIL) COOs"),
                    ("FA_SIL_COC", "Firearms and Ammunition (SIL) COCs"),
                    ("FA_SIL_COO", "Firearms and Ammunition (SIL) COOs"),
                    ("SANCTIONS_COC_COO", "Adhoc application countries"),
                    ("SANCTIONS", "Sanctions and adhoc licence countries"),
                    ("WOOD_COO", "Wood (Quota) COOs"),
                    ("EU", "All EU countries"),
                    ("NON_EU", "Non EU Single Countries"),
                    (
                        "CPTPP",
                        "Comprehensive and Progressive Agreement for Trans-Pacific Partnership",
                    ),
                    ("DEROGATION_COO", "Derogation from Sanctions COOs"),
                    ("IRON_COO", "Iron and Steel (Quota) COOs"),
                    ("OPT_COO", "OPT COOs"),
                    ("OPT_TEMP_EXPORT_COO", "OPT Temp Export COOs"),
                    ("TEXTILES_COO", "Textile COOs"),
                ],
                max_length=255,
                unique=True,
                verbose_name="Group Name",
            ),
        ),
    ]