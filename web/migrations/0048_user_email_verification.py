# Generated by Django 5.1.3 on 2024-12-06 12:19

import uuid

import django.db.models.deletion
from django.db import migrations, models

from web.mail.constants import EmailTypes

GOV_NOTIFY_TEMPLATE_ID = "b6a91535-7d3e-43b6-971f-6ab3ef64ae52"  # /PS-IGNORE


def add_email_verification_template(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    EmailTemplate = apps.get_model("web", "EmailTemplate")
    EmailTemplate.objects.using(db_alias).get_or_create(
        name=EmailTypes.EMAIL_VERIFICATION,
        gov_notify_template_id=GOV_NOTIFY_TEMPLATE_ID,
    )


def remove_email_verification_template(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    EmailTemplate = apps.get_model("web", "EmailTemplate")
    EmailTemplate.objects.using(db_alias).filter(
        name=EmailTypes.EMAIL_VERIFICATION, gov_notify_template_id=GOV_NOTIFY_TEMPLATE_ID
    ).delete()


def mark_primary_email_address_as_verified(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Email = apps.get_model("web", "Email")
    Email.objects.using(db_alias).filter(is_primary=True).update(is_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0047_ecilexample"),
    ]

    operations = [
        migrations.RunPython(add_email_verification_template, remove_email_verification_template),
        migrations.AddField(
            model_name="email",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="emailtemplate",
            name="name",
            field=models.CharField(
                choices=[
                    ("ACCESS_REQUEST", "Access Request"),
                    ("ACCESS_REQUEST_CLOSED", "Access Request Closed"),
                    ("ACCESS_REQUEST_APPROVAL_COMPLETE", "Access Request Approval Complete"),
                    ("APPLICATION_COMPLETE", "Application Complete"),
                    (
                        "APPLICATION_VARIATION_REQUEST_COMPLETE",
                        "Application Variation Request Complete",
                    ),
                    ("APPLICATION_EXTENSION_COMPLETE", "Application Extension Complete"),
                    ("APPLICATION_STOPPED", "Application Stopped"),
                    ("APPLICATION_REFUSED", "Application Refused"),
                    ("APPLICATION_REASSIGNED", "Application Reassigned"),
                    ("APPLICATION_REOPENED", "Application Reopened"),
                    ("APPLICATION_UPDATE", "Application Update"),
                    ("APPLICATION_UPDATE_RESPONSE", "Application Update Response"),
                    ("APPLICATION_UPDATE_WITHDRAWN", "Application Update Withdrawn"),
                    (
                        "EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED",
                        "Exporter Access Request Approval Opened",
                    ),
                    (
                        "IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED",
                        "Importer Access Request Approval Opened",
                    ),
                    ("FIREARMS_SUPPLEMENTARY_REPORT", "Firearms Supplementary Report"),
                    ("CONSTABULARY_DEACTIVATED_FIREARMS", "Constabulary Deactivated Firearms"),
                    ("WITHDRAWAL_ACCEPTED", "Withdrawal Accepted"),
                    ("WITHDRAWAL_CANCELLED", "Withdrawal Cancelled"),
                    ("WITHDRAWAL_OPENED", "Withdrawal Opened"),
                    ("WITHDRAWAL_REJECTED", "Withdrawal Rejected"),
                    (
                        "APPLICATION_VARIATION_REQUEST_CANCELLED",
                        "Application Variation Request Cancelled",
                    ),
                    (
                        "APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED",
                        "Application Variation Request Update Required",
                    ),
                    (
                        "APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED",
                        "Application Variation Request Update Cancelled",
                    ),
                    (
                        "APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED",
                        "Application Variation Request Update Received",
                    ),
                    (
                        "APPLICATION_VARIATION_REQUEST_REFUSED",
                        "Application Variation Request Refused",
                    ),
                    ("CASE_EMAIL", "Case Email"),
                    ("CASE_EMAIL_WITH_DOCUMENTS", "Case Email With Documents"),
                    (
                        "APPLICATION_FURTHER_INFORMATION_REQUEST",
                        "Application Further Information Request",
                    ),
                    (
                        "APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED",
                        "Application Further Information Request Responded",
                    ),
                    (
                        "APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN",
                        "Application Further Information Request Withdrawn",
                    ),
                    (
                        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST",
                        "Application Further Information Request",
                    ),
                    (
                        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED",
                        "Access Request Further Information Request Responded",
                    ),
                    (
                        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN",
                        "Access Request Further Information Request Withdrawn",
                    ),
                    ("LICENCE_REVOKED", "Licence Revoked"),
                    ("CERTIFICATE_REVOKED", "Certificate Revoked"),
                    ("AUTHORITY_ARCHIVED", "Authority Archived"),
                    ("AUTHORITY_EXPIRING_SECTION_5", "Authority Expiring Section 5"),
                    ("AUTHORITY_EXPIRING_FIREARMS", "Authority Expiring Firearms"),
                    ("MAILSHOT", "Mailshot"),
                    ("RETRACT_MAILSHOT", "Retract Mailshot"),
                    ("NEW_USER_WELCOME", "New User Welcome"),
                    ("ORG_CONTACT_INVITE", "New Organisation Contact Invite"),
                    ("EMAIL_VERIFICATION", "Email Verification"),
                ],
                max_length=255,
                unique=True,
            ),
        ),
        migrations.CreateModel(
            name="EmailVerification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("processed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("verified_at", models.DateTimeField(auto_now=True)),
                (
                    "email",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="web.email"),
                ),
            ],
        ),
        migrations.RunPython(mark_primary_email_address_as_verified, migrations.RunPython.noop),
    ]