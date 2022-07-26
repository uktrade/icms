from django.db import models

from .base import MigrationBase


class Process(MigrationBase):
    PROCESS_PK = True

    process_type = models.CharField(max_length=50, default=None)
    is_active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True)
    ima_id = models.IntegerField(null=True, unique=True)

    @classmethod
    def get_excludes(cls):
        return ["ima_id"]
