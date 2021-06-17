from django.db import models

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import (
    ApplicationBase,
    CaseNote,
    UpdateRequest,
    VariationRequest,
)
from web.domains.country.models import Country, CountryGroup
from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User


class ExportApplicationType(models.Model):
    class Types(models.TextChoices):
        FREE_SALE = ("CFS", "Certificate of Free Sale")
        MANUFACTURE = ("COM", "Certificate of Manufacture")

    class ProcessTypes(models.TextChoices):
        COM = ("CertificateOfManufactureApplication", "Certificate of Manufacture")
        CFS = ("CertificateOfFreeSaleApplication", "Certificate of Free Sale")

    is_active = models.BooleanField(blank=False, null=False, default=True)
    type_code = models.CharField(
        max_length=30, blank=False, null=False, unique=True, choices=Types.choices
    )
    type = models.CharField(max_length=70, blank=False, null=False)
    allow_multiple_products = models.BooleanField(blank=False, null=False)
    generate_cover_letter = models.BooleanField(blank=False, null=False)
    allow_hse_authorization = models.BooleanField(blank=False, null=False)
    country_group = models.ForeignKey(
        CountryGroup, on_delete=models.PROTECT, blank=False, null=False
    )
    country_group_for_manufacture = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="manufacture_export_application_types",
    )

    def get_type_description(self):
        return self.get_type_code_display()

    def __str__(self):
        return f"{self.type}"

    class Meta:
        ordering = ("type",)


class ExportApplication(ApplicationBase):
    application_type = models.ForeignKey(
        ExportApplicationType, on_delete=models.PROTECT, blank=False, null=False
    )

    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)

    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False, related_name="updated_export_cases"
    )

    variation_requests = models.ManyToManyField(VariationRequest)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    case_notes = models.ManyToManyField(CaseNote)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="submitted_export_application",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_export_applications",
    )

    exporter = models.ForeignKey(
        Exporter,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="export_applications",
    )

    exporter_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=False,
        null=True,
        related_name="office_export_applications",
    )

    contact = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contact_export_applications",
    )

    countries = models.ManyToManyField(Country)

    agent = models.ForeignKey(
        Exporter,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_export_applications",
    )
    agent_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_office_export_applications",
    )
    case_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    def is_import_application(self) -> bool:
        return False

    def get_edit_view_name(self) -> str:
        if self.process_type == ExportApplicationType.ProcessTypes.COM:
            return "export:com-edit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    def get_workbasket_subject(self) -> str:
        return "\n".join(
            [
                "Certificate Application",
                ExportApplicationType.ProcessTypes(self.process_type).label,
            ]
        )


class CertificateOfManufactureApplication(ExportApplication):
    PROCESS_TYPE = ExportApplicationType.ProcessTypes.COM

    is_pesticide_on_free_sale_uk = models.BooleanField(null=True)
    is_manufacturer = models.BooleanField(null=True)

    product_name = models.CharField(max_length=1000, blank=False)
    chemical_name = models.CharField(max_length=500, blank=False)
    manufacturing_process = models.TextField(max_length=4000, blank=False)


# TODO: add certificate of free sale model
