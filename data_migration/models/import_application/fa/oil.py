from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import File
from data_migration.models.import_application.import_application import (
    ChecklistBase,
    ImportApplication,
)

from .authorities import FirearmsAuthority
from .base import (
    FirearmBase,
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)


class OpenIndividualLicenceApplication(FirearmBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    section1 = models.BooleanField(default=False)
    section2 = models.BooleanField(default=False)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "OILSupplementaryInfo"]


class ChecklistFirearmsOILApplication(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.PROTECT,
        to_field="imad_id",
        related_name="+",
    )

    authority_required = models.CharField(
        max_length=3,
        null=True,
    )
    authority_received = models.CharField(
        max_length=3,
        null=True,
    )
    authority_police = models.CharField(
        max_length=3,
        null=True,
    )

    @classmethod
    def y_n_fields(cls) -> list[str]:
        fields = super().y_n_fields()
        return fields + ["authority_required", "authority_received", "authority_police"]


class OILSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="+",
        to_field="imad_id",
    )


class OILApplicationFirearmAuthority(MigrationBase):
    openindividuallicenceapplication = models.ForeignKey(
        OpenIndividualLicenceApplication, on_delete=models.CASCADE
    )
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)


class OILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        OILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class OILSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        OILSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)
