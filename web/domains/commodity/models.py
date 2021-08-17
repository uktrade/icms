from django.db import models

from web.domains.country.models import Country
from web.models.mixins import Archivable


class Unit(models.Model):
    unit_type = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    short_description = models.CharField(max_length=30)
    hmrc_code = models.IntegerField()

    def __str__(self):
        return self.description


class CommodityType(models.Model):
    type_code = models.CharField(max_length=20)
    type = models.CharField(max_length=50)

    def __str__(self):
        return self.type


class Commodity(Archivable, models.Model):
    is_active = models.BooleanField(default=True)
    commodity_code = models.CharField(max_length=10)
    validity_start_date = models.DateField()
    validity_end_date = models.DateField(blank=True, null=True)
    quantity_threshold = models.IntegerField(blank=True, null=True)
    sigl_product_type = models.CharField(max_length=3, blank=True, null=True)

    commodity_type = models.ForeignKey(CommodityType, on_delete=models.PROTECT)

    # These are to be ignored, the start_datetime is simply a timestamp.
    start_datetime = models.DateTimeField(auto_now_add=True)
    # When the record is archived.
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.commodity_code

    class Meta:
        ordering = (
            "-is_active",
            "commodity_code",
        )


class CommodityGroup(Archivable, models.Model):
    AUTO = "AUTO"
    CATEGORY = "CATEGORY"

    TYPES = [(AUTO, "Auto"), (CATEGORY, ("Category"))]

    is_active = models.BooleanField(default=True)
    group_type = models.CharField(max_length=20, choices=TYPES, default=AUTO)
    group_code = models.CharField(max_length=25)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.CharField(max_length=4000, blank=True, null=True)
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.PROTECT, blank=True, null=True
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, blank=True, null=True)
    commodities = models.ManyToManyField(Commodity, blank=True)

    # A timestamp when the record was created
    start_datetime = models.DateTimeField(auto_now_add=True)
    # When the record is archived.
    end_datetime = models.DateTimeField(blank=True, null=True)

    @property
    def group_type_verbose(self):
        return self.get_group_type_display()

    @property
    def commodity_type_verbose(self):
        return self.commodity_type.type

    def __str__(self):
        if self.group_name:
            return f"{self.group_code} - {self.group_name}"
        else:
            return self.group_code

    class Meta:
        ordering = (
            "-is_active",
            "group_code",
        )


class Usage(models.Model):
    application_type = models.ForeignKey("web.ImportApplicationType", on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.PROTECT, related_name="usages"
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    maximum_allocation = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ("application_type", "country", "start_date")

    def __str__(self):
        return (
            f"Usage(application_type={self.application_type}"
            f", country={self.country}"
            f", commodity_group={self.commodity_group}"
            f")"
        )
