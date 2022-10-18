from django.db import models

from .base import MigrationBase


class Process(MigrationBase):
    PROCESS_PK = True

    process_type = models.CharField(max_length=50, default=None)
    is_active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True)
    ima_id = models.IntegerField(null=True, unique=True)
    ca_id = models.IntegerField(null=True, unique=True)

    @classmethod
    def get_excludes(cls):
        return ["ima_id", "ca_id", "uref"]


class WorkBasket(MigrationBase):
    ima = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        null=True,
        to_field="ima_id",
        related_name="ima_workbasket",
    )
    ca = models.ForeignKey(
        Process, on_delete=models.CASCADE, null=True, to_field="ca_id", related_name="ca_workbasket"
    )
    is_active = models.BooleanField()
    action_mnem = models.CharField(max_length=50)
    action_description = models.CharField(max_length=100)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True)
