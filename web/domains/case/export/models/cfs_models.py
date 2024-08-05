from typing import final

from django.conf import settings
from django.db import models

from web.flow.models import ProcessTypes
from web.models.shared import AddressEntryType, YesNoChoices
from web.types import TypedTextChoices

from .common_models import ExportApplication


class CertificateOfFreeSaleApplicationABC(models.Model):
    class Meta:
        abstract = True


@final
class CertificateOfFreeSaleApplication(  # type: ignore[misc]
    ExportApplication, CertificateOfFreeSaleApplicationABC
):
    PROCESS_TYPE = ProcessTypes.CFS
    IS_FINAL = True


class CFSScheduleABC(models.Model):
    class Meta:
        abstract = True

    class ExporterStatus(TypedTextChoices):
        IS_MANUFACTURER = ("MANUFACTURER", "I am the manufacturer")
        IS_NOT_MANUFACTURER = ("NOT_MANUFACTURER", "I am not the manufacturer")

    class ProductEligibility(TypedTextChoices):
        SOLD_ON_UK_MARKET = (
            "SOLD_ON_UK_MARKET",
            "The products are currently sold on the UK market",
        )
        MEET_UK_PRODUCT_SAFETY = (
            "MEET_UK_PRODUCT_SAFETY",
            "The products meet the product safety requirements to be sold on the UK market",
        )

    exporter_status = models.CharField(
        null=True,
        default=None,
        verbose_name="Exporter Status",
        choices=ExporterStatus.choices,
        max_length=16,
    )

    brand_name_holder = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Are you the Brand name holder?",
    )

    legislations = models.ManyToManyField(
        "web.ProductLegislation",
        verbose_name="Legislation",
        help_text=(
            "Enter legislation relevant to the products on this schedule. A"
            " maximum of 3 pieces of legislation may be added per schedule. If"
            " you cannot find relevant legislation, please contact DIT,"
            " enquiries.ilb@trade.gov.uk, to request to have it added."  # /PS-IGNORE
        ),
    )

    biocidal_claim = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        blank=True,
        default=None,
        verbose_name="Do you products make any biocidal claims?",
    )

    product_eligibility = models.CharField(
        null=True,
        default=None,
        verbose_name="Product Eligibility",
        max_length=22,
        choices=ProductEligibility.choices,
        help_text=(
            f"If your products are currently for export only, you MUST select {ProductEligibility.MEET_UK_PRODUCT_SAFETY.label}"
        ),
    )

    goods_placed_on_uk_market = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Have you placed the goods on the UK market or intend to place on UK market in future?",
    )

    goods_export_only = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Are these goods for export only and will never be placed by you on the UK market?",
    )

    any_raw_materials = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Are any of the products raw materials?",
        help_text="Only choose 'Yes' if the product is a material used in the manufacture of a finished product.",
    )

    final_product_end_use = models.CharField(
        null=True, blank=True, max_length=4000, verbose_name="End Use or Final Product"
    )

    country_of_manufacture = models.ForeignKey(
        "web.Country",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Country Of Manufacture",
        help_text="You can only list one country. Add another schedule if product information differs.",
    )

    schedule_statements_accordance_with_standards = models.BooleanField(
        default=False,
        verbose_name="Schedule Statements",
    )

    schedule_statements_is_responsible_person = models.BooleanField(default=False, verbose_name="")

    # "Manufactured at" section fields
    manufacturer_name = models.CharField(max_length=200, verbose_name="Name", null=True)

    manufacturer_address_entry_type = models.CharField(
        max_length=10,
        choices=AddressEntryType.choices,
        verbose_name="Address Type",
        default=AddressEntryType.SEARCH,
    )

    manufacturer_postcode = models.CharField(
        max_length=30, verbose_name="Postcode", null=True, blank=True
    )

    manufacturer_address = models.CharField(
        max_length=300, verbose_name="Address", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_biocidal(self) -> bool:
        return self.legislations.filter(is_biocidal=True).exists()

    def is_biocidal_claim(self) -> bool:
        return self.legislations.filter(is_biocidal_claim=True).exists()


class CFSSchedule(CFSScheduleABC):
    application = models.ForeignKey(
        "web.CertificateOfFreeSaleApplication",
        related_name="schedules",
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="+",
    )


class CFSProductABC(models.Model):
    class Meta:
        abstract = True

    product_name = models.CharField(max_length=1000)


class CFSProduct(CFSProductABC):
    schedule = models.ForeignKey(
        "web.CFSSchedule", related_name="products", on_delete=models.CASCADE
    )


class CFSProductTypeABC(models.Model):
    class Meta:
        abstract = True

    product_type_number = models.IntegerField(choices=[(i, i) for i in range(1, 23)])


class CFSProductType(CFSProductTypeABC):
    product = models.ForeignKey(
        "web.CFSProduct", related_name="product_type_numbers", on_delete=models.CASCADE
    )


class CFSProductActiveIngredientABC(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=500)
    cas_number = models.CharField(
        max_length=50,
        verbose_name="CAS Number",
        help_text=(
            "A CAS (Chemical Abstracts Service) Registry Number is a unique chemical identifier."
            " Numbers must be separated by hyphens."
            " For example, the CAS number for caffeine is 58-08-2."
        ),
    )


class CFSProductActiveIngredient(CFSProductActiveIngredientABC):
    product = models.ForeignKey(
        "web.CFSProduct", related_name="active_ingredients", on_delete=models.CASCADE
    )
