from django.contrib.postgres.fields import ArrayField
from django.db import models

from web.domains.country.models import Country
from web.models.mixins import Archivable


class Unit(models.Model):
    unit_type = models.CharField(max_length=20, blank=False, null=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    short_description = models.CharField(max_length=30, blank=False, null=False)
    hmrc_code = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return self.description


class CommodityType(models.Model):
    COMMODITY_TYPES = [
        "Chemicals",
        "Firearms and Ammunition",
        "Iron, Steel and Aluminium",
        "Oil and Petrochemicals",
        "Precious Metals and Stones",
        "Textiles",
        "Vehicles",
        "Wood",
        "Wood Charcoal",
    ]
    COMMODITY_TYPE_CHOICES = ((val, val) for val in COMMODITY_TYPES)

    allowed_codes = ArrayField(models.CharField(max_length=10), blank=True, null=True)
    type = models.CharField(max_length=50, choices=COMMODITY_TYPE_CHOICES)

    def __str__(self):
        return self.type


class Commodity(Archivable, models.Model):
    LABEL = "Commodity"

    is_active = models.BooleanField(blank=False, null=False, default=True)
    start_datetime = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    commodity_code = models.CharField(max_length=10, blank=False, null=False)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.PROTECT, blank=True, null=True
    )
    validity_start_date = models.DateField(blank=False, null=True)
    validity_end_date = models.DateField(blank=True, null=True)
    quantity_threshold = models.IntegerField(blank=True, null=True)
    sigl_product_type = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        if self.id:
            return f"{self.LABEL} - {self.commodity_code}"
        else:
            return self.LABEL

    class Meta:
        ordering = (
            "-is_active",
            "commodity_code",
        )


class CommodityGroup(Archivable, models.Model):
    LABEL = "Commodity Group"

    AUTO = "AUTO"
    CATEGORY = "CATEGORY"

    TYPES = [(AUTO, "Auto"), (CATEGORY, ("Category"))]

    is_active = models.BooleanField(blank=False, null=False, default=True)
    start_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    group_type = models.CharField(
        max_length=20, choices=TYPES, blank=False, null=False, default=AUTO
    )
    group_code = models.CharField(max_length=25, blank=False, null=False)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.CharField(max_length=4000, blank=True, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.PROTECT, blank=True, null=True
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, blank=True, null=True)
    commodities = models.ManyToManyField(Commodity, blank=True)

    @property
    def group_type_verbose(self):
        return dict(CommodityGroup.TYPES)[self.group_type]

    @property
    def commodity_type_verbose(self):
        return self.commodity_type.type

    def __str__(self):
        if self.id:
            return f"{self.LABEL} - {self.group_code}"
        else:
            return self.LABEL

    class Meta:
        ordering = (
            "-is_active",
            "group_code",
        )


class Usage(models.Model):
    application_type = models.ForeignKey("web.ImportApplicationType", on_delete=models.PROTECT)
    application_subtype = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=False, null=False)
    commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.PROTECT, related_name="usages"
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True)
    maximum_allocation = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ("-start_datetime",)
