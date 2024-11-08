from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import FileTarget
from data_migration.models.reference import Commodity, CommodityGroup

from .import_application import ChecklistBase, ImportApplication, ImportApplicationBase


class WoodQuotaApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    shipping_year = models.IntegerField(null=True)
    exporter_name = models.CharField(max_length=100, null=True)
    exporter_address = models.CharField(max_length=4000, null=True)
    exporter_vat_nr = models.CharField(max_length=100, null=True)
    commodity = models.ForeignKey(Commodity, on_delete=models.PROTECT, null=True, related_name="+")
    goods_description = models.CharField(max_length=100, null=True)
    goods_qty = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    goods_unit = models.CharField(max_length=40, null=True)
    additional_comments = models.CharField(max_length=4000, null=True)
    contract_files_xml = models.TextField(null=True)
    export_certs_xml = models.TextField(null=True)


class WoodContractFile(MigrationBase):
    import_application = models.ForeignKey(WoodQuotaApplication, on_delete=models.CASCADE)
    target = models.ForeignKey(FileTarget, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100)
    contract_date = models.DateField()


class WoodQuotaChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )

    sigl_wood_application_logged = models.CharField(max_length=5, null=True)


class TextilesApplication(ImportApplicationBase):
    imad = models.OneToOneField(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    category_licence_description = models.CharField(null=True, max_length=4000)
    goods_cleared = models.CharField(max_length=5, null=True)
    goods_description = models.CharField(max_length=100, null=True)
    quantity = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    shipping_year = models.PositiveSmallIntegerField(null=True)
    category_commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.PROTECT, null=True, related_name="+"
    )
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    contract_files_xml = models.TextField(null=True)


class TextilesChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )

    within_maximum_amount_limit = models.CharField(max_length=5, null=True)
