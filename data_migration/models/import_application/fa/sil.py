from django.db import models

from ..import_application import ImportApplication
from .base import FirearmBase, SupplementaryInfoBase, SupplementaryReportBase


class SILApplication(FirearmBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", unique=True
    )
    section1 = models.BooleanField(default=False)
    section2 = models.BooleanField(default=False)
    section5 = models.BooleanField(default=False)
    section58_obsolete = models.BooleanField(default=False)
    section58_other = models.BooleanField(default=False)
    other_description = models.CharField(max_length=4000, null=True)
    military_police = models.BooleanField(null=True)
    eu_single_market = models.BooleanField(null=True)
    manufactured = models.BooleanField(null=True)
    additional_comments = models.CharField(max_length=4000, null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "SILSupplementaryInfo"]


# TODO ICMSLST-1548: SILUserSection5 M2M
# TODO ICMSLST-1548: Section5Authority M2M
# TODO ICMSLST-1548: FirearmAuthorityM2M


class SILSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="+",
        to_field="imad_id",
    )


class SILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        SILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )
