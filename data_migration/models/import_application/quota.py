from typing import Any

from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import File
from data_migration.models.reference import Commodity, CommodityGroup
from data_migration.utils.format import str_to_bool

from .import_application import ChecklistBase, ImportApplication, ImportApplicationBase

# TODO ICMSLST-1496: Add wood supporting documents and contract documents
# TODO ICMSLST-1496: Add textiles supporting documents


class WoodContractFile(MigrationBase):
    file_ptr = models.ForeignKey(File, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100)
    contract_date = models.DateField()


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


class WoodQuotaChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )

    sigl_wood_application_logged = models.CharField(max_length=5, null=True)

    @classmethod
    def bool_fields(cls) -> list[str]:
        return super().bool_fields() + ["sigl_wood_application_logged"]


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

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["goods_cleared"] = str_to_bool(data["goods_cleared"])
        return data


class TextilesChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )

    within_maximum_amount_limit = models.CharField(max_length=5, null=True)

    @classmethod
    def bool_fields(cls) -> list[str]:
        return super().bool_fields() + ["within_maximum_amount_limit"]
