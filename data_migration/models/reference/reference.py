from django.db import models

from data_migration.models.base import MigrationBase


class UniqueReference(MigrationBase):
    prefix = models.CharField(max_length=8)
    year = models.IntegerField(null=True)
    reference_no = models.IntegerField(null=True)
    uref = models.CharField(max_length=16, unique=True, null=True)
