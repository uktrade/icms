from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase
from data_migration.models.flow import Process

from .user import Exporter, Importer, User


class AccessRequest(MigrationBase):
    PROCESS_PK = True

    iar = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="accessrequest", to_field="iar_id"
    )
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=30)
    request_type = models.CharField(max_length=30)
    organisation_name = models.CharField(max_length=100)
    organisation_address = models.TextField(null=True)
    request_reason = models.TextField(null=True)
    agent_name = models.CharField(max_length=100, null=True)
    agent_address = models.TextField(null=True)
    submit_datetime = models.DateTimeField()
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="submitted_access_requests",
    )
    last_update_datetime = models.DateTimeField()
    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="updated_access_requests"
    )
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="closed_access_requests"
    )
    response = models.CharField(max_length=20, null=True)
    response_reason = models.TextField(null=True)
    importer = models.ForeignKey(Importer, on_delete=models.CASCADE, null=True)
    exporter = models.ForeignKey(Exporter, on_delete=models.CASCADE, null=True)
    request_type = models.CharField(max_length=30)
    fir_xml = models.TextField(null=True)
    approval_xml = models.TextField(null=True)

    # eori number and organisation registered number not found in source data

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        for k in ("agent_address", "request_reason", "response_reason", "organisation_address"):
            data[k] = data.pop(k) or ""

        return data

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", cls.__name__]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "id",
            "iar_id",
            "importer_id",
            "exporter_id",
            "request_type",
        ]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"process_ptr_id": F("id")}


class ImporterAccessRequest(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            AccessRequest.objects.filter(
                request_type__in=["MAIN_IMPORTER_ACCESS", "AGENT_IMPORTER_ACCESS"]
            )
            .values("request_type", accessrequest_ptr_id=F("id"), link_id=F("importer__id"))
            .iterator(chunk_size=2000)
        )


class ExporterAccessRequest(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            AccessRequest.objects.filter(
                request_type__in=["MAIN_EXPORTER_ACCESS", "AGENT_EXPORTER_ACCESS"]
            )
            .values("request_type", accessrequest_ptr_id=F("id"), link_id=F("exporter__id"))
            .iterator(chunk_size=2000)
        )


class ApprovalRequest(MigrationBase):
    PROCESS_PK = True

    access_request = models.ForeignKey(
        AccessRequest, on_delete=models.CASCADE, related_name="approval_requests"
    )

    status = models.CharField(max_length=20, null=True)
    request_date = models.DateTimeField(null=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name="approval_requests"
    )
    requested_from = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="assigned_approval_requests",
    )
    response = models.CharField(max_length=20, null=True)
    response_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="responded_approval_requests",
    )
    response_date = models.DateTimeField(null=True)
    response_reason = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"process_ptr_id": F("id")}


class ImporterApprovalRequest(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            ApprovalRequest.objects.filter(
                access_request__request_type__in=["MAIN_IMPORTER_ACCESS", "AGENT_IMPORTER_ACCESS"]
            )
            .values(approvalrequest_ptr_id=F("id"))
            .iterator(chunk_size=2000)
        )


class ExporterApprovalRequest(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            ApprovalRequest.objects.filter(
                access_request__request_type__in=["MAIN_EXPORTER_ACCESS", "AGENT_EXPORTER_ACCESS"]
            )
            .values(approvalrequest_ptr_id=F("id"))
            .iterator(chunk_size=2000)
        )
