from django.db import models

from web.domains.case.export.models import ExportApplicationType
from web.domains.user.models import User


class CertificateApplicationTemplate(models.Model):
    class SharingStatuses(models.TextChoices):
        PRIVATE = ("private", "Private (do not share)")
        VIEW = ("view", "Share (view only)")
        EDIT = ("edit", "Share (allow edit)")

    name = models.CharField(
        verbose_name="Template Name",
        max_length=70,
        help_text=(
            "DIT does not issue Certificates of Free Sale for food, food supplements, pesticides"
            " and CE marked medical devices. Certificates of Manufacture are applicable only to"
            " pesticides that are for export only and not on free sale on the domestic market."
        ),
    )

    description = models.CharField(verbose_name="Template Description", max_length=500)

    application_type = models.CharField(
        verbose_name="Application Type", max_length=3, choices=ExportApplicationType.Types.choices
    )

    sharing = models.CharField(
        max_length=7,
        choices=SharingStatuses.choices,
        help_text=(
            "Whether or not other contacts of exporters/agents you are a contact of should"
            " be able view and create applications using this template, and if they can edit it."
        ),
    )

    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
