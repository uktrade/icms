from typing import Any, Generator

from django.db import models
from django.db.models import OuterRef, Subquery

from data_migration.models.file import File, FileM2MBase, FileTarget, MigrationBase
from data_migration.models.reference import Commodity
from data_migration.utils.format import str_to_bool, validate_int

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

    @classmethod
    def get_source_data(cls) -> Generator:
        sub_query = File.objects.filter(target_id=OuterRef("target_id"))

        return (
            cls.objects.filter(file_type__isnull=False)
            .annotate(file_ptr_id=Subquery(sub_query.values("pk")[:1]))
            .exclude(file_ptr_id__isnull=True)
            .values("file_ptr_id", "file_type")
            .iterator()
        )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["file_type"] = data["file_type"].lower()
        return data


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

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["customs_cleared_to_uk"] = str_to_bool(data["customs_cleared_to_uk"])
        validate_int(["quantity", "value_gbp", "value_eur"], data)

        return data

    @classmethod
    def get_source_data(cls) -> Generator:
        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()
        related = cls.get_related()
        sub_query = File.objects.filter(target_id=OuterRef("imad__sps_contract_file__target_id"))

        return (
            cls.objects.select_related(*related)
            .annotate(contract_file_id=Subquery(sub_query.values("pk")[:1]))
            .values("contract_file_id", *values, **values_kwargs)
            .iterator()
        )

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return super().models_to_populate() + ["PriorSurveillanceContractFile"]


class SPSSupportingDoc(FileM2MBase):
    APP_MODEL = "priorsurveillanceapplication"

    class Meta:
        abstract = True
