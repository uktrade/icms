from django.db import models
from web.domains.case.export.models import ExportCase
from web.domains.country.models import Country, CountryGroup
from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User


class ExportApplicationType(models.Model):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    type_code = models.CharField(max_length=30, blank=False, null=False)
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


class ExportApplication(models.Model):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    application_type = models.ForeignKey(
        ExportApplicationType, on_delete=models.PROTECT, blank=False, null=False
    )
    case = models.OneToOneField(
        ExportCase, on_delete=models.PROTECT, related_name="application", blank=True, null=True
    )
    submit_datetime = models.DateTimeField(blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
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
