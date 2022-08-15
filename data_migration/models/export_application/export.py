from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase
from data_migration.models.reference import CountryGroup


class ExportApplicationType(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    type_code = models.CharField(max_length=30, null=False, unique=True)
    type = models.CharField(max_length=70, null=False)
    allow_multiple_products = models.BooleanField(null=False)
    generate_cover_letter = models.BooleanField(null=False)
    allow_hse_authorization = models.BooleanField(null=False)
    country_group_legacy = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        null=False,
        related_name="+",
        to_field="country_group_id",
    )
    country_of_manufacture_cg = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        to_field="country_group_id",
    )

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["country_group_legacy_id", "country_of_manufacture_cg_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "country_group_id": F("country_group_legacy__id"),
            "country_group_for_manufacture_id": F("country_of_manufacture_cg__id"),
        }
