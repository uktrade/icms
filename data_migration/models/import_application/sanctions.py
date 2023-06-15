from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import FileM2MBase
from data_migration.models.reference import Commodity

from .import_application import ImportApplication, ImportApplicationBase


class SanctionsAndAdhocApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    exporter_name = models.CharField(max_length=4096, null=True)
    exporter_address = models.CharField(max_length=4096, null=True)
    commodities_xml = models.TextField(null=True)


class SanctionsAndAdhocApplicationGoods(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.CASCADE)
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    goods_description = models.CharField(max_length=4096)
    quantity_amount = models.DecimalField(max_digits=14, decimal_places=3)
    value = models.DecimalField(max_digits=12, decimal_places=2)


class SanctionsAndAdhocSupportingDoc(FileM2MBase):
    APP_MODEL = "sanctionsandadhocapplication"

    class Meta:
        abstract = True
