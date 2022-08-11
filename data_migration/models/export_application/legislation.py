from django.db import models

from data_migration.models.base import MigrationBase


class ProductLegislation(MigrationBase):
    name = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    is_biocidal = models.BooleanField(default=False)
    is_eu_cosmetics_regulation = models.BooleanField(default=False)
    is_biocidal_claim = models.BooleanField(default=False)
    gb_legislation = models.BooleanField(default=True)
    ni_legislation = models.BooleanField(default=True)
