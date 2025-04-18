# Generated by Django 5.1.7 on 2025-03-31 13:25
from django.db import migrations, models

from web.domains.template.constants import TemplateCodes


def create_nuclear_materials_email_template(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Template = apps.get_model("web", "Template")
    TemplateVersion = apps.get_model("web", "TemplateVersion")

    new_template = Template.objects.using(db_alias).create(
        is_active=True,
        template_name="Nuclear Materials Email",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_code=TemplateCodes.IMA_NMIL_EMAIL,
    )

    TemplateVersion.objects.using(db_alias).create(
        template=new_template,
        created_by_id=0,
        title="Nuclear materials import licence [[CASE_REFERENCE]]",
        content=(
            "Dear colleagues\n\n"
            "We have received a nuclear materials import licence application from:\n"
            "[[IMPORTER_NAME]]\n"
            "[[IMPORTER_ADDRESS]]\n\n"
            "The application is for:\n\n"
            "[[GOODS_DESCRIPTION]]\n\n"
            "Nature of business: [[NATURE_OF_BUSINESS]]\n"
            "Consigner company name: [[CONSIGNOR_NAME]]\n"
            "Consignor company address and postcode: [[CONSIGNOR_ADDRESS]]\n"
            "End user company name: [[END_USER_NAME]]\n"
            "End user company address and postcode: [[END_USER_ADDRESS]]\n"
            "Intended end use of shipment: [[INTENDED_USE_OF_SHIPMENT]]\n"
            "Licence type: [[LICENCE_TYPE]]\n"
            "Date of first shipment: [[SHIPMENT_START_DATE]]\n"
            "Date of last shipment: [[SHIPMENT_END_DATE]]\n"
            "Contact information for security team: [[SECURITY_TEAM_CONTACT_INFORMATION]]\n\n"
            "Yours sincerely,\n\n"
            "[[CASE_OFFICER_NAME]]\n"
            "[[CASE_OFFICER_EMAIL]]\n"
            "[[CASE_OFFICER_PHONE]]\n"
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0066_nuclearmaterialapplication_dates_and_unlimited_goods"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caseemail",
            name="template_code",
            field=models.CharField(
                choices=[
                    ("CA_BEIS_EMAIL", "Business, Energy & Industrial Strategy Email"),
                    ("IMA_CONSTAB_EMAIL", "Constabulary Email"),
                    ("CA_HSE_EMAIL", "Health and Safety Email"),
                    ("IMA_NMIL_EMAIL", "Nuclear Materials Email"),
                    ("IMA_SANCTIONS_EMAIL", "Sanctions Email"),
                    ("DEACTIVATE_USER", "Deactivate User Email"),
                    ("REACTIVATE_USER", "Reactivate User Email"),
                ],
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="NuclearMaterialEmail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, verbose_name="Email Address")),
                ("created_datetime", models.DateTimeField(auto_now_add=True)),
                ("updated_datetime", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.RunPython(
            create_nuclear_materials_email_template, reverse_code=migrations.RunPython.noop
        ),
    ]
