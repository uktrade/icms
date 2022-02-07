from typing import Any

from django.db import models

from .base import MigrationBase

# Country Data


class Country(MigrationBase):
    name = models.CharField(max_length=4000, blank=False, null=False)
    status = models.CharField(max_length=10, blank=False, null=False)
    type = models.CharField(max_length=30, blank=False, null=False)
    commission_code = models.CharField(max_length=20, blank=False, null=False)
    hmrc_code = models.CharField(max_length=20, blank=False, null=False)

    def excludes(self) -> list[str]:
        return super().excludes() + ["status"]

    def data_export(self) -> dict[str, Any]:
        data = super().data_export()
        data["is_active"] = self.status.lower() == "active"
        return data


class CountryGroup(MigrationBase):
    name = models.CharField(max_length=4000, blank=False, null=False, unique=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)


class CountryGroupCountry(MigrationBase):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    countrygroup = models.ForeignKey(CountryGroup, on_delete=models.CASCADE)


class CountryTranslationSet(MigrationBase):
    name = models.CharField(max_length=100, blank=False, null=False)
    status = models.CharField(max_length=10, blank=False, null=False)

    def excludes(self) -> list[str]:
        return super().excludes() + ["status"]

    def data_export(self) -> dict[str, Any]:
        data = super().data_export()
        data["is_active"] = self.status.lower() == "active"
        return data


class CountryTranslation(MigrationBase):
    translation = models.CharField(max_length=150, blank=False, null=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=False, null=False)
    translation_set = models.ForeignKey(CountryTranslationSet, on_delete=models.CASCADE)


# Commodity Data


class Unit(MigrationBase):
    unit_type = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100)
    short_description = models.CharField(max_length=30)
    hmrc_code = models.IntegerField()


class CommodityType(MigrationBase):
    type_code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=50)


class Commodity(MigrationBase):
    status = models.CharField(max_length=10, blank=False, null=False)
    commodity_code = models.CharField(max_length=10)
    validity_start_date = models.DateField()
    validity_end_date = models.DateField(null=True)
    quantity_threshold = models.IntegerField(null=True)
    sigl_product_type = models.CharField(max_length=3, blank=True, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.CASCADE, to_field="type_code"
    )
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)

    def excludes(self) -> list[str]:
        return super().excludes() + ["status"]

    def data_export(self) -> dict[str, Any]:
        data = super().data_export()
        data["is_active"] = self.status.lower() == "active"
        data["commodity_type_id"] = self.commodity_type.pk
        return data


class CommodityGroup(MigrationBase):
    status = models.CharField(max_length=10, blank=False, null=False)
    group_type = models.CharField(max_length=20)
    group_code = models.CharField(max_length=25)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.CharField(max_length=4000, blank=True, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.CASCADE, to_field="type_code"
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, to_field="unit_type", null=True)
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)

    def excludes(self) -> list[str]:
        return super().excludes() + ["status"]

    def data_export(self) -> dict[str, Any]:
        data = super().data_export()
        data["is_active"] = self.status.lower() == "active"
        data["commodity_type_id"] = self.commodity_type.pk
        data["unit_id"] = self.unit and self.unit.pk
        return data


class CommodityGroupCommodity(MigrationBase):
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    commoditygroup = models.ForeignKey(CommodityGroup, on_delete=models.CASCADE)


# TODO: ICMSLST-1422 Populate usage data
class Usage(MigrationBase):
    application_type_id = models.IntegerField()
    country_id = models.IntegerField()
    commodity_group_id = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    maximum_allocation = models.IntegerField(null=True)
