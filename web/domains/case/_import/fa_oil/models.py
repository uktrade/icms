from django.db import models

from web.models import UserImportCertificate
from web.models.shared import YesNoNAChoices

from ..models import ChecklistBase, ImportApplication


class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = "OpenIndividualLicenceApplication"

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)

    know_bought_from = models.BooleanField(null=True)

    user_imported_certificates = models.ManyToManyField(UserImportCertificate, related_name="+")

    commodity_code = models.CharField(max_length=40, blank=False, null=True)


class VerifiedCertificate(models.Model):
    import_application = models.ForeignKey(
        OpenIndividualLicenceApplication,
        on_delete=models.PROTECT,
        related_name="verified_certificates",
    )
    firearms_authority = models.ForeignKey(
        "FirearmsAuthority", on_delete=models.PROTECT, related_name="verified_certificates"
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class ChecklistFirearmsOILApplication(ChecklistBase):
    import_application = models.OneToOneField(
        OpenIndividualLicenceApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    authority_required = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess required?",
    )
    authority_received = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess received?",
    )
    authority_police = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess checked with police?",
    )
