from typing import final

from django.db import models

from web.domains.case._import.fa.models import (
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)
from web.domains.case._import.models import ChecklistBase, ImportApplication
from web.flow.models import ProcessTypes
from web.models import UserImportCertificate
from web.models.shared import FirearmCommodity, YesNoNAChoices


@final
class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.FA_OIL
    IS_FINAL = True

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)

    know_bought_from = models.BooleanField(null=True)

    user_imported_certificates = models.ManyToManyField(
        UserImportCertificate, related_name="oil_application"
    )
    verified_certificates = models.ManyToManyField(
        "FirearmsAuthority", related_name="oil_application"
    )

    commodity_code = models.CharField(
        max_length=40,
        null=True,
        choices=FirearmCommodity.choices,
        verbose_name="Commodity Code",
        help_text=(
            "You must pick the commodity code group that applies to the items that you wish to"
            ' import. Please note that "ex Chapter 97" is only relevant to collectors pieces and'
            " items over 100 years old. Please contact HMRC classification advisory service,"
            " 01702 366077, if you are unsure of the correct code."
        ),
    )


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


class OILSupplementaryInfo(SupplementaryInfoBase):
    import_application = models.OneToOneField(
        OpenIndividualLicenceApplication,
        on_delete=models.CASCADE,
        related_name="supplementary_info",
    )


class OILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        OILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class OILSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        OILSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )
