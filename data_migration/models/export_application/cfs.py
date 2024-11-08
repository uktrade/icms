from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.reference import Country
from data_migration.models.user import User

from .export import ExportApplication, ExportBase
from .legislation import ProductLegislation


class CertificateOfFreeSaleApplication(ExportBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")


class CFSSchedule(MigrationBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    schedule_ordinal = models.PositiveIntegerField()
    exporter_status = models.CharField(null=True, max_length=16)
    brand_name_holder = models.CharField(max_length=3, null=True)
    product_eligibility = models.CharField(null=True, max_length=22)
    goods_placed_on_uk_market = models.CharField(max_length=3, null=True)
    goods_export_only = models.CharField(max_length=3, null=True)
    any_raw_materials = models.CharField(max_length=3, null=True)
    final_product_end_use = models.CharField(null=True, max_length=4000)
    country_of_manufacture = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )
    accordance_with_standards = models.BooleanField(default=False)
    is_responsible_person = models.BooleanField(default=False)
    manufacturer_name = models.CharField(max_length=200, null=True)
    manufacturer_address_type = models.CharField(max_length=10)
    manufacturer_postcode = models.CharField(max_length=30, null=True)
    manufacturer_address = models.CharField(max_length=4000, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True)
    product_xml = models.TextField(null=True)
    legislation_xml = models.TextField(null=True)


class CFSProduct(MigrationBase):
    schedule = models.ForeignKey(CFSSchedule, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=1000)
    product_type_xml = models.TextField(null=True)
    active_ingredient_xml = models.TextField(null=True)


class CFSProductType(MigrationBase):
    product_type_number = models.IntegerField()
    product = models.ForeignKey(CFSProduct, on_delete=models.CASCADE)


class CFSProductActiveIngredient(MigrationBase):
    name = models.CharField(max_length=500)
    cas_number = models.CharField(max_length=50)
    product = models.ForeignKey(CFSProduct, on_delete=models.CASCADE)


class CFSLegislation(MigrationBase):
    cfsschedule = models.ForeignKey(CFSSchedule, on_delete=models.CASCADE)
    productlegislation = models.ForeignKey(ProductLegislation, on_delete=models.CASCADE)
