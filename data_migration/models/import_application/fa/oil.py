from django.db import models

from data_migration.models.base import File
from data_migration.models.import_application.import_application import (
    ChecklistBase,
    ImportApplication,
    ImportApplicationBase,
)

from .base import (
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)

# TODO ICMSLST-1496: M2M to UserImportCertificate
# TODO ICMSLST-1496: M2M to FirearmsAuthority


class OpenIndividualLicenceApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    section1 = models.BooleanField(default=False)
    section2 = models.BooleanField(default=False)
    know_bought_from = models.BooleanField(null=True)
    commodity_code = models.CharField(max_length=40, null=True)
    commodities_xml = models.TextField(null=True)
    constabulary_certs_xml = models.TextField(null=True)
    fa_authorities_xml = models.TextField(null=True)
    bought_from_details_xml = models.TextField(null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "OILSupplementaryInfo"]


class ChecklistFirearmsOILApplication(ChecklistBase):
    import_application = models.OneToOneField(
        OpenIndividualLicenceApplication,
        on_delete=models.PROTECT,
    )

    authority_required = models.CharField(
        max_length=10,
        null=True,
    )
    authority_received = models.CharField(
        max_length=10,
        null=True,
    )
    authority_police = models.CharField(
        max_length=10,
        null=True,
    )


class OILSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        OpenIndividualLicenceApplication,
        on_delete=models.CASCADE,
        related_name="supplementary_info",
        to_field="imad_id",
    )
    supplementary_report_xml = models.TextField(null=True)


class OILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        OILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class OILSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        OILSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)
