# Generated by Django 5.1.5 on 2025-01-20 13:34

import django.contrib.postgres.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0051_email_verified_reminder_count"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserFeedbackSurvey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "satisfaction",
                    models.CharField(
                        choices=[
                            ("VERY_DISSATISFIED", "Very dissatisfied"),
                            ("DISSATISFIED", "Dissatisfied"),
                            ("NEITHER", "Neither dissatisfied or satisfied"),
                            ("SATISFIED", "Satisfied"),
                            ("VERY_SATISFIED", "Very satisfied"),
                        ],
                        max_length=18,
                        verbose_name="Overall satisfaction with the service",
                    ),
                ),
                (
                    "issues",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("UNABLE_TO_FIND", "I did not find what I was looking for"),
                                ("NAVIGATION", "I found it difficult to navigate the service"),
                                ("LACKS_FEATURE", "The service lacks a feature I need"),
                                (
                                    "UNABLE_TO_LOAD",
                                    "I was not able to load, refresh, or enter a page",
                                ),
                                ("OTHER", "Other"),
                                ("NO", "I did not experience any issues"),
                            ],
                            max_length=16,
                        ),
                        blank=True,
                        default=list,
                        size=None,
                        verbose_name="Did you experience any of the following issues?",
                    ),
                ),
                (
                    "issue_details",
                    models.TextField(
                        blank=True, default="", verbose_name="Tell us more about the issue you had."
                    ),
                ),
                (
                    "find_service",
                    models.CharField(
                        choices=[
                            ("VERY_EASY", "Very Easy"),
                            ("EASY", "Easy"),
                            ("NEITHER", "Neither easy or difficult"),
                            ("DIFFICULT", "Difficult"),
                            ("VERY_DIFFICULT", "Very difficult"),
                        ],
                        max_length=16,
                        verbose_name="How was the process of finding the service?",
                    ),
                ),
                (
                    "find_service_details",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="Tell us why the service was not easy to find.",
                    ),
                ),
                (
                    "additional_support",
                    models.CharField(
                        choices=[
                            ("NO", "No, I didn’t need any additional support "),
                            ("EMAILED", "Yes, I emailed asking for additional support"),
                            ("COULD_NOT_FIND", "Yes, but I could not find any additional support"),
                            ("DONT_KNOW", "I don’t know "),
                        ],
                        max_length=16,
                        verbose_name="Did you need any additional support at any point during the application?",
                    ),
                ),
                (
                    "service_improvements",
                    models.TextField(
                        blank=True, default="", verbose_name="How could we improve the service?"
                    ),
                ),
                (
                    "future_contact",
                    models.CharField(
                        choices=[("yes", "Yes"), ("no", "No")],
                        max_length=3,
                        verbose_name="Would you be happy for us to contact you in the future to help us improve the service?",
                    ),
                ),
                ("site", models.CharField(max_length=60)),
                ("created_datetime", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "process",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="web.process"
                    ),
                ),
            ],
        ),
    ]
