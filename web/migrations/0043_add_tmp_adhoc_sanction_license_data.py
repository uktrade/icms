from django.db import migrations


def add_import_data(apps, schema_editor):
    ImportApplicationType = apps.get_model("web", "ImportApplicationType")

    # TODO: this is a placeholder for the missing data in the legacy system
    ImportApplicationType.objects.create(
        is_active=True,
        type="SAN_ADHOC_TEMP",
        sub_type="SAN_TEMP",
        licence_type_code="SANCTIONS_ADHOC",
        sigl_flag=False,
        chief_flag=True,
        chief_licence_prefix="GBSAN_TEMP",
        paper_licence_flag=False,
        electronic_licence_flag=True,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=True,
        endorsements_flag=False,
        quantity_unlimited_flag=False,
        unit_list_csv="KGS,BARRELS",
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/ApplyingForSanctionsLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0042_endorsementimportapplication"),
    ]

    operations = [
        migrations.RunPython(add_import_data),
    ]
