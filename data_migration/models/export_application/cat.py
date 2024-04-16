from typing import Any

from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.export_application.cfs import ProductLegislation
from data_migration.models.reference import Country
from data_migration.models.user import User


class CertificateApplicationTemplate(MigrationBase):
    name = models.CharField(max_length=70)
    description = models.CharField(max_length=500)
    application_type = models.CharField(max_length=3)
    sharing = models.CharField(max_length=7)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    created_datetime = models.DateTimeField()
    last_updated_datetime = models.DateTimeField()
    is_active = models.BooleanField()


class CertificateOfManufactureApplicationTemplate(MigrationBase):
    template = models.OneToOneField(
        CertificateApplicationTemplate, on_delete=models.CASCADE, related_name="com_template"
    )
    is_free_sale_uk = models.BooleanField(null=True)
    is_manufacturer = models.BooleanField(null=True)
    product_name = models.CharField(max_length=1000, null=True)
    chemical_name = models.CharField(max_length=500, null=True)
    manufacturing_process = models.TextField(max_length=4000, null=True)
    countries_xml = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["is_free_sale_uk"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "is_pesticide_on_free_sale_uk": models.F("is_free_sale_uk"),
        }


class COMTemplateCountries(MigrationBase):
    certificateofmanufactureapplicationtemplate = models.ForeignKey(
        CertificateOfManufactureApplicationTemplate, on_delete=models.CASCADE
    )
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class CertificateOfFreeSaleApplicationTemplate(MigrationBase):
    template = models.OneToOneField(
        CertificateApplicationTemplate, on_delete=models.CASCADE, related_name="cfs_template"
    )
    countries_xml = models.TextField(null=True)
    schedules_xml = models.TextField(null=True)


class CFSScheduleTemplate(MigrationBase):
    exporter_status = models.CharField(null=True, max_length=16)
    brand_name_holder = models.CharField(max_length=3, null=True)
    biocidal_claim = models.CharField(max_length=3, null=True)
    product_eligibility = models.CharField(null=True, max_length=22)
    goods_placed_on_uk_market = models.CharField(max_length=3, null=True)
    goods_export_only = models.CharField(max_length=3, null=True)
    any_raw_materials = models.CharField(max_length=3, null=True)
    final_product_end_use = models.CharField(null=True, max_length=4000)
    country_of_manufacture = models.ForeignKey(Country, on_delete=models.PROTECT, null=True)
    schedule_statements_accordance_with_standards = models.BooleanField(default=False)
    schedule_statements_is_responsible_person = models.BooleanField(default=False)
    manufacturer_name = models.CharField(max_length=200, null=True)
    manufacturer_address_entry_type = models.CharField(max_length=10)
    manufacturer_postcode = models.CharField(max_length=30, null=True)
    manufacturer_address = models.CharField(max_length=4000, null=True)
    product_xml = models.TextField(null=True)
    legislation_xml = models.TextField(null=True)
    application = models.ForeignKey(
        CertificateOfFreeSaleApplicationTemplate,
        related_name="schedules",
        on_delete=models.CASCADE,
    )

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "created_by_id": models.F("application__template__owner_id"),
        }


class CFSTemplateCountries(MigrationBase):
    certificateoffreesaleapplicationtemplate = models.ForeignKey(
        CertificateOfFreeSaleApplicationTemplate, on_delete=models.CASCADE
    )
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class CFSProductTemplate(MigrationBase):
    product_name = models.CharField(max_length=1000)
    schedule = models.ForeignKey(
        CFSScheduleTemplate, related_name="products", on_delete=models.CASCADE
    )
    product_type_xml = models.TextField(null=True)
    active_ingredient_xml = models.TextField(null=True)


class CFSProductTypeTemplate(MigrationBase):
    product_type_number = models.IntegerField()
    product = models.ForeignKey(
        CFSProductTemplate, related_name="product_type_numbers", on_delete=models.CASCADE
    )


class CFSProductActiveIngredientTemplate(MigrationBase):
    name = models.CharField(max_length=500)
    cas_number = models.CharField(max_length=50)
    product = models.ForeignKey(
        CFSProductTemplate, related_name="active_ingredients", on_delete=models.CASCADE
    )


class CFSTemplateLegislation(MigrationBase):
    cfsschedule = models.ForeignKey(CFSScheduleTemplate, on_delete=models.CASCADE)
    productlegislation = models.ForeignKey(ProductLegislation, on_delete=models.CASCADE)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["cfsschedule_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "cfsscheduletemplate_id": models.F("cfsschedule_id"),
        }
