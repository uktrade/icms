from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase
from data_migration.models.reference import (
    CommodityGroup,
    CommodityType,
    Country,
    CountryGroup,
)
from data_migration.models.template import Template


class ImportApplicationType(MigrationBase):
    is_active = models.BooleanField()
    type = models.CharField(max_length=70)
    sub_type = models.CharField(max_length=70, null=True)
    name = models.CharField(max_length=100)
    licence_type_code = models.CharField(max_length=20)
    sigl_flag = models.CharField(max_length=5)
    chief_flag = models.CharField(max_length=5)
    chief_licence_prefix = models.CharField(max_length=10, null=True)
    paper_licence_flag = models.CharField(max_length=5)
    electronic_licence_flag = models.CharField(max_length=5)
    cover_letter_flag = models.CharField(max_length=5)
    cover_letter_schedule_flag = models.CharField(max_length=5)
    category_flag = models.CharField(max_length=5)
    sigl_category_prefix = models.CharField(max_length=100, null=True)
    chief_category_prefix = models.CharField(max_length=10, null=True)
    default_licence_length_months = models.IntegerField(null=True)
    default_commodity_desc = models.CharField(max_length=200, null=True)
    quantity_unlimited_flag = models.CharField(max_length=5)
    unit_list_csv = models.CharField(max_length=200, null=True)
    exp_cert_upload_flag = models.CharField(max_length=5)
    supporting_docs_upload_flag = models.CharField(max_length=5)
    multiple_commodities_flag = models.CharField(max_length=5)
    guidance_file_url = models.CharField(max_length=4000, null=True)
    licence_category_description = models.CharField(max_length=1000, null=True)
    usage_auto_category_desc_flag = models.CharField(max_length=5)
    case_checklist_flag = models.CharField(max_length=5)
    importer_printable = models.CharField(max_length=5)
    origin_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        related_name="+",
        to_field="country_group_id",
        null=True,
    )
    consignment_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        related_name="+",
        to_field="country_group_id",
        null=True,
    )
    master_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        related_name="+",
        to_field="country_group_id",
        null=True,
    )
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.PROTECT, to_field="type_code", related_name="+", null=True
    )
    declaration_template_code = models.ForeignKey(
        Template, on_delete=models.PROTECT, null=True, to_field="template_code"
    )
    default_commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.SET_NULL, to_field="group_code", null=True
    )

    @staticmethod
    def get_excludes() -> list[str]:
        return ["declaration_template_code_id"]

    @staticmethod
    def get_includes() -> list[str]:
        return [
            "commodity_type__id",
            "consignment_country_group__id",
            "default_commodity_group__id",
            "master_country_group__id",
            "origin_country_group__id",
        ]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"declaration_template_id": F("declaration_template_code__id")}

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["sub_type"] = (data["type"] == "FA" and data["sub_type"]) or None
        data["importer_printable"] = data["importer_printable"].lower() == "true"

        for field in data.keys():
            if field.endswith("_flag"):
                data[field] = data[field].lower() == "true"

        return data


class Usage(MigrationBase):
    application_type = models.ForeignKey(ImportApplicationType, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    maximum_allocation = models.IntegerField(null=True)
