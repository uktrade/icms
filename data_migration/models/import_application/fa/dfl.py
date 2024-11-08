from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileTarget
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


class DFLGoodsCertificate(MigrationBase):
    target = models.ForeignKey(FileTarget, related_name="+", on_delete=models.PROTECT)
    dfl_application = models.ForeignKey(
        DFLApplication,
        on_delete=models.PROTECT,
        related_name="+",
    )
    goods_description_original = models.CharField(max_length=4096, null=True)
    goods_description = models.CharField(max_length=4096, null=True)
    deactivated_certificate_reference = models.CharField(max_length=50, null=True)
    legacy_ordinal = models.IntegerField(null=True)

    issuing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )


class DFLChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", related_name="+"
    )
    certificate_attached = models.CharField(max_length=3, null=True)
    certificate_issued = models.CharField(max_length=3, null=True)


class DFLSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="+",
        to_field="imad_id",
    )


class DFLSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        DFLSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class DFLSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        DFLSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    goods_certificate_legacy_id = models.IntegerField()
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")
