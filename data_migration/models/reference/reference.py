from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase


class UniqueReference(MigrationBase):
    prefix = models.CharField(max_length=8)
    year = models.IntegerField(null=True)
    reference_no = models.IntegerField(null=True)
    uref = models.CharField(max_length=16, unique=True, null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["reference_no", "uref"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"reference": F("reference_no")}

    @classmethod
    def get_source_data(cls) -> Generator:
        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()
        return (
            cls.objects.exclude(prefix="COVER")
            .order_by("pk")
            .values("prefix", "year", "reference_no")
            .distinct()
            .values(*values, **values_kwargs)
            .iterator(chunk_size=2000)
        )
