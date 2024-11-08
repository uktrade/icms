from django.db import models

from data_migration.models.file import FileTarget, MigrationBase
from data_migration.models.reference import Commodity

from .import_application import ImportApplication, ImportApplicationBase


class PriorSurveillanceContractFile(MigrationBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="sps_contract_file",
        to_field="imad_id",
    )
    file_type = models.CharField(max_length=32, null=True)
    target = models.OneToOneField(
        FileTarget, on_delete=models.CASCADE, related_name="sps_contract_file"
    )


class PriorSurveillanceApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    customs_cleared_to_uk = models.CharField(max_length=10, null=True)
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    quantity = models.CharField(max_length=100, null=True)
    value_gbp = models.CharField(max_length=100, null=True)
    value_eur = models.CharField(max_length=100, null=True)
