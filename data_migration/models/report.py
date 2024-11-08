from django.db import models

from data_migration.models import File, User

from .base import MigrationBase


class ScheduleReport(MigrationBase):
    report_domain = models.CharField(max_length=300)
    title = models.CharField(max_length=400)
    notes = models.TextField(blank=True, null=True)
    parameters_xml = models.TextField(null=True)
    scheduled_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    parameters = models.JSONField(null=True)


class GeneratedReport(MigrationBase):
    schedule = models.ForeignKey(ScheduleReport, on_delete=models.CASCADE)
    report_output = models.ForeignKey(File, on_delete=models.PROTECT, to_field="report_output_id")
