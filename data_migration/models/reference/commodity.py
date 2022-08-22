from django.db import models

from data_migration.models.base import MigrationBase


class Unit(MigrationBase):
    unit_type = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100)
    short_description = models.CharField(max_length=30)
    hmrc_code = models.IntegerField()


class CommodityType(MigrationBase):
    type_code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=50)


class Commodity(MigrationBase):
    is_active = models.BooleanField(default=True)
    commodity_code = models.CharField(max_length=10)
    validity_start_date = models.DateField()
    validity_end_date = models.DateField(null=True)
    quantity_threshold = models.IntegerField(null=True)
    sigl_product_type = models.CharField(max_length=3, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.CASCADE, to_field="type_code"
    )
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)

    @staticmethod
    def get_includes() -> list[str]:
        return ["commodity_type__id"]


class CommodityGroup(MigrationBase):
    is_active = models.BooleanField(default=True)
    group_type = models.CharField(max_length=20)
    group_code = models.CharField(max_length=25, unique=True)
    group_name = models.CharField(max_length=100, null=True)
    group_description = models.CharField(max_length=4000, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.CASCADE, to_field="type_code"
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, to_field="unit_type", null=True)
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)

    @staticmethod
    def get_includes() -> list[str]:
        return ["commodity_type__id", "unit__id"]


class CommodityGroupCommodity(MigrationBase):
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    commoditygroup = models.ForeignKey(CommodityGroup, on_delete=models.CASCADE)
