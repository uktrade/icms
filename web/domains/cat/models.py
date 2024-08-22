from django.conf import settings
from django.db import models

from web.domains.case.export.models import (
    CertificateOfFreeSaleApplicationABC,
    CertificateOfGoodManufacturingPracticeApplicationABC,
    CertificateOfManufactureApplicationABC,
    CFSProductABC,
    CFSProductActiveIngredientABC,
    CFSProductTypeABC,
    CFSScheduleABC,
    ExportApplicationABC,
)
from web.models import ExportApplicationType
from web.types import TypedTextChoices


class CertificateApplicationTemplate(models.Model):
    class SharingStatuses(TypedTextChoices):
        PRIVATE = ("PRIVATE", "Private (do not share)")
        VIEW = ("VIEW", "Share (view only)")
        EDIT = ("EDIT", "Share (allow edit)")

    class CountryType(TypedTextChoices):
        GB = ("GB", "Great Britain")
        NIR = ("NIR", "Northern Ireland")

    name = models.CharField(verbose_name="Template Name", max_length=70)

    description = models.CharField(verbose_name="Template Description", max_length=500)

    application_type = models.CharField(
        verbose_name="Application Type",
        max_length=3,
        choices=ExportApplicationType.Types.choices,
        help_text=(
            "DIT does not issue Certificates of Free Sale for food, food supplements, pesticides"
            " and CE marked medical devices. Certificates of Manufacture are applicable only to"
            " pesticides that are for export only and not on free sale on the domestic market."
        ),
    )
    # CFS template specific field
    template_country = models.CharField(
        max_length=3,
        choices=CountryType.choices,
        verbose_name="Template Country",
        help_text="Country where the goods will be exported from.",
        default=None,
        blank=True,
        null=True,
    )

    sharing = models.CharField(
        max_length=7,
        choices=SharingStatuses.choices,
        help_text=(
            "Whether or not other contacts of exporters/agents you are a contact of should"
            " be able view and create applications using this template, and if they can edit it."
        ),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_datetime = models.DateTimeField(auto_now_add=True)
    last_updated_datetime = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    @property
    def is_ni_template(self) -> bool:
        return self.template_country == self.CountryType.NIR


class CertificateOfManufactureApplicationTemplate(  # type: ignore[misc]
    ExportApplicationABC, CertificateOfManufactureApplicationABC
):
    template = models.OneToOneField(
        "web.CertificateApplicationTemplate", on_delete=models.CASCADE, related_name="com_template"
    )


class CertificateOfFreeSaleApplicationTemplate(  # type: ignore[misc]
    ExportApplicationABC, CertificateOfFreeSaleApplicationABC
):
    template = models.OneToOneField(
        "web.CertificateApplicationTemplate", on_delete=models.CASCADE, related_name="cfs_template"
    )


class CFSScheduleTemplate(CFSScheduleABC):
    application = models.ForeignKey(
        "web.CertificateOfFreeSaleApplicationTemplate",
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


class CFSProductTemplate(CFSProductABC):
    schedule = models.ForeignKey(
        "web.CFSScheduleTemplate", related_name="products", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "product_name"],
                name="template_schedule_and_product_name_unique",
            ),
        ]


class CFSProductTypeTemplate(CFSProductTypeABC):
    product = models.ForeignKey(
        "web.CFSProductTemplate", related_name="product_type_numbers", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "product_type_number"], name="template_product_and_ptn_unique"
            ),
        ]


class CFSProductActiveIngredientTemplate(CFSProductActiveIngredientABC):
    product = models.ForeignKey(
        "web.CFSProductTemplate", related_name="active_ingredients", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "cas_number"], name="template_product_and_cas_unique"
            ),
            models.UniqueConstraint(
                fields=["product", "name"], name="template_product_and_name_unique"
            ),
        ]


class CertificateOfGoodManufacturingPracticeApplicationTemplate(  # type: ignore[misc]
    ExportApplicationABC, CertificateOfGoodManufacturingPracticeApplicationABC
):
    template = models.OneToOneField(
        "web.CertificateApplicationTemplate", on_delete=models.CASCADE, related_name="gmp_template"
    )
