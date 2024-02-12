from datetime import datetime

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from .constants import ReportStatus, ReportType


class Report(models.Model):
    name = models.CharField(max_length=400)
    description = models.TextField()
    report_type = models.CharField(max_length=120, choices=ReportType.choices, unique=True)

    @property
    def last_run_completed_at(self) -> datetime | None:
        last_run = self.schedules.order_by("-finished_at").first()
        if last_run and last_run.finished_at:
            return last_run.finished_at
        return None

    def __str__(self):
        return self.get_report_type_display()


class ScheduleReport(models.Model):
    title = models.CharField(max_length=400)
    notes = models.TextField(blank=True, null=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="schedules")
    parameters = models.JSONField(encoder=DjangoJSONEncoder)
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        choices=ReportStatus.choices,
        default=ReportStatus.SUBMITTED,
    )

    def __str__(self):
        return f"{self.report.get_report_type_display()} - Schedule:{self.pk}"


class GeneratedReport(models.Model):
    schedule = models.ForeignKey(
        ScheduleReport, on_delete=models.CASCADE, related_name="generated_files"
    )
    document = models.OneToOneField("web.File", on_delete=models.CASCADE, null=True)
    status = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        choices=ReportStatus.choices,
        default=ReportStatus.SUBMITTED,
    )
