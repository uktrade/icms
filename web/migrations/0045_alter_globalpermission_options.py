# Generated by Django 4.2.16 on 2024-11-13 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0044_alter_accessrequest_submit_datetime"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="globalpermission",
            options={
                "default_permissions": [],
                "managed": False,
                "permissions": [
                    ("can_view_permission_harness", "Can view the permission test harness"),
                    ("can_view_l10n_harness", "Can view the L10N test harness"),
                    ("can_view_importer_details", "Can view the importer details list page."),
                    ("can_view_exporter_details", "Can view the exporter details list page."),
                    ("can_view_import_case_search", "Can view search import applications page"),
                    (
                        "can_view_export_case_search",
                        "Can view search certificate applications page",
                    ),
                    ("view_imi", "Can view IMI pages."),
                    (
                        "can_view_documents_constabulary",
                        "Can view issued documents within constabulary region page",
                    ),
                    ("can_view_report_issued_certificates", "Can view Issued Certificate Report"),
                    ("can_view_report_access_requests", "Can view Access Requests Report"),
                    ("can_view_report_import_licences", "Can view Import Licences Report"),
                    (
                        "can_view_report_supplementary_firearms",
                        "Can view Supplementary Firearms Report",
                    ),
                    ("can_view_report_firearms_licences", "Can view Firearms Licences Report"),
                    ("can_view_report_active_users", "Can view Active Users Report"),
                    (
                        "can_view_one_login_test_account_setup",
                        "Can view One Login Test Account Setup",
                    ),
                    ("importer_access", "Can act as an importer"),
                    ("exporter_access", "Can act as an exporter"),
                    ("ilb_admin", "Is an ILB administrator"),
                    ("sanctions_case_officer", "Is a sanctions caseworker"),
                    ("importer_regulator", "Is an Importer Regulator"),
                    ("importer_admin", "Can manage Importer records."),
                    ("exporter_admin", "Can manage Exporter records."),
                    ("commodity_admin", "Is a commodity administrator"),
                    ("manage_sanction_contacts", "Manage sanction email contacts"),
                    ("manage_signatures", "Manage signatures"),
                    ("access_reports", "Access reports"),
                    ("edit_firearm_authorities", "Can edit Importer Verified Firearms Authorities"),
                    (
                        "edit_section_5_firearm_authorities",
                        "Can edit Importer Verified Section 5 Firearm Authorities",
                    ),
                    ("search_all_cases", "Can search across all cases."),
                    ("is_icms_data_admin", "Can maintain data in the ICMS admin site."),
                    ("view_ecil_prototype", "Can view ECIL prototype."),
                ],
            },
        ),
    ]