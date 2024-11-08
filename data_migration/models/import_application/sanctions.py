from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.reference import Commodity

from .import_application import ImportApplication, ImportApplicationBase


class SanctionsAndAdhocApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    exporter_name = models.CharField(max_length=4096, null=True)
    exporter_address = models.CharField(max_length=4096, null=True)
    commodities_xml = models.TextField(null=True)
    commodities_response_xml = models.TextField(null=True)


class SanctionsAndAdhocApplicationGoods(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.CASCADE)
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    goods_description = models.CharField(max_length=4096, null=True)
    quantity_amount = models.DecimalField(max_digits=14, decimal_places=3, null=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    goods_description_original = models.CharField(max_length=4096, null=True)
    quantity_amount_original = models.DecimalField(max_digits=14, decimal_places=3, null=True)
    value_original = models.DecimalField(max_digits=12, decimal_places=2, null=True)
