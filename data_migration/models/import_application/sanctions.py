from typing import Any

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

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["goods_description"] = data["goods_description"] or data["goods_description_original"]
        data["quantity_amount"] = data["quantity_amount"] or data["quantity_amount_original"]
        data["value"] = data["value"] or data["value_original"]
        return data


class SanctionsAndAdhocSupportingDoc(FileM2MBase):
    APP_MODEL = "sanctionsandadhocapplication"

    @classmethod
    def get_m2m_filter_kwargs(cls) -> dict[str, Any]:
        filter_kwargs = super().get_m2m_filter_kwargs()

        # Exclude docs that don't have an associated sanctions application
        filter_kwargs["target__folder__import_application__isnull"] = False

        return filter_kwargs

    class Meta:
        abstract = True
