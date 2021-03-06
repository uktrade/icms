# Generated by Django 3.1.2 on 2020-11-20 13:54

import django.db.models.deletion
from django.db import migrations, models

import web.domains.workbasket.base


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0002_fir_ordering"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalRequest",
            fields=[
                (
                    "process_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="web.process",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("DRAFT", "DRAFT"),
                            ("OPEN", "OPEN"),
                            ("CANCELLED", "CANCELLED"),
                            ("COMPLETED", "COMPLETED"),
                        ],
                        default="OPEN",
                        max_length=20,
                        null=True,
                    ),
                ),
                ("request_date", models.DateTimeField(auto_now_add=True, null=True)),
                (
                    "response",
                    models.CharField(
                        blank=True,
                        choices=[("APPROVE", "Approve"), ("REFUSE", "Refuse")],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("response_date", models.DateTimeField(blank=True, null=True)),
                ("response_reason", models.CharField(blank=True, max_length=4000, null=True)),
                (
                    "access_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="approval_requests",
                        to="web.accessrequest",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="approval_requests",
                        to="web.user",
                    ),
                ),
                (
                    "requested_from",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assigned_approval_requests",
                        to="web.user",
                    ),
                ),
                (
                    "response_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responded_approval_requests",
                        to="web.user",
                    ),
                ),
            ],
            options={
                "ordering": ("-request_date",),
            },
            bases=(web.domains.workbasket.base.WorkbasketBase, "web.process"),
        ),
        migrations.CreateModel(
            name="ExporterApprovalRequest",
            fields=[
                (
                    "approvalrequest_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="web.approvalrequest",
                    ),
                ),
            ],
            bases=("web.approvalrequest",),
        ),
        migrations.CreateModel(
            name="ImporterApprovalRequest",
            fields=[
                (
                    "approvalrequest_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="web.approvalrequest",
                    ),
                ),
            ],
            bases=("web.approvalrequest",),
        ),
    ]
