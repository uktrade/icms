from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import File
from data_migration.models.import_application.import_application import (
    ChecklistBase,
    ImportApplication,
)
from data_migration.models.reference.country import Country
from data_migration.models.reference.fa import Constabulary

from .base import (
    FirearmBase,
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)


class DFLApplication(FirearmBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", unique=True
    )
    deactivated_firearm = models.BooleanField(default=True)
    proof_checked = models.BooleanField(default=False)
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "DFLSupplementaryInfo"]


class DFLGoodsCertificate(MigrationBase):
    file_pkr = models.ForeignKey(File, related_name="+", on_delete=models.PROTECT)
    imad = models.ForeignKey(
        DFLApplication,
        on_delete=models.PROTECT,
        related_name="goods_certificates",
        to_field="imad_id",
    )
    goods_description = models.CharField(max_length=4096)
    deactivated_certificate_reference = models.CharField(max_length=50)

    issuing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="+",
        null=False,
    )


class DFLChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        DFLApplication, on_delete=models.PROTECT, to_field="imad_id"
    )
    deactivation_certificate_attached = models.CharField(max_length=3, null=True)
    deactivation_certificate_issued = models.CharField(max_length=3, null=True)


class DFLSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        DFLApplication,
        on_delete=models.CASCADE,
        related_name="supplementary_info",
        to_field="imad_id",
    )


# TODO ICMSLST-1506 - Handle migration of DFL supplementary reports


class DFLSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        DFLSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class DFLSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        DFLSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    goods_certificate_legacy_id = models.IntegerField()
    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)
