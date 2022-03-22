from django.db import models

from data_migration.models.base import MigrationBase


class Constabulary(MigrationBase):
    name = models.CharField(max_length=50, null=False)
    region = models.CharField(max_length=3, null=False)
    email = models.EmailField(max_length=254, null=False)
    is_active = models.BooleanField(null=False, default=True)
