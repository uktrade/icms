from django.db import models

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
