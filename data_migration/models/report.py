from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models import File, User

from .base import MigrationBase

ANONYMOUS_USER_PK = 0


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

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        reports = {
            "IMP_ISSUED_CERTIFICATES": 1,
            "IMP_DATA_EXTRACT": 3,
            "ACCESS_REQUEST_REPORT": 2,
            "IMP_FIREARMS_LICENCES": 5,
            "IMP_FA_SUPPLEMENTARY_REPORTS_NCA": 4,
        }

        data["report_id"] = reports[data.pop("report_domain")]
        data["status"] = "COMPLETED"
        data["legacy_report_id"] = data["id"]
        data["parameters"]["is_legacy_report"] = True

        data["scheduled_by_id"] = ANONYMOUS_USER_PK
        if data["deleted_by_id"]:
            data["deleted_by_id"] = ANONYMOUS_USER_PK
        return data


class GeneratedReport(MigrationBase):
    schedule = models.ForeignKey(ScheduleReport, on_delete=models.CASCADE)
    report_output = models.ForeignKey(File, on_delete=models.PROTECT, to_field="report_output_id")

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["status"] = "COMPLETED"
        return data

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"document_id": F("report_output__id")}

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["File", cls.__name__]

    @classmethod
    def get_excludes(cls):
        return ["report_output_id"]
