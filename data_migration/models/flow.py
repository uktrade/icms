from django.db import models

from data_migration import queries

from .base import MigrationBase


class Process(MigrationBase):
    PROCESS_PK = True
    UPDATE_TIMESTAMP_QUERY = queries.process_timestamp_update

    process_type = models.CharField(max_length=50, default=None)
    is_active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField()
    finished = models.DateTimeField(null=True)

    # import application id
    ima_id = models.IntegerField(null=True, unique=True)

    # certificate (export) application id
    ca_id = models.IntegerField(null=True, unique=True)

    # access request id
    iar_id = models.IntegerField(null=True, unique=True)

    @classmethod
    def get_excludes(cls):
        return ["ima_id", "ca_id", "iar_id"]
