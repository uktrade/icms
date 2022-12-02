from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import OuterRef, Q, Subquery

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

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "DFLSupplementaryInfo"]


class DFLGoodsCertificate(MigrationBase):
    target = models.ForeignKey(FileTarget, related_name="+", on_delete=models.PROTECT)
    dfl_application = models.ForeignKey(
        DFLApplication,
        on_delete=models.PROTECT,
        related_name="+",
    )
    goods_description = models.CharField(max_length=4096, null=True)
    deactivated_certificate_reference = models.CharField(max_length=50, null=True)
    legacy_id = models.IntegerField(null=True)

    issuing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values() + ["file_ptr_id"]
        sub_query = File.objects.filter(target_id=OuterRef("target_id"))

        # Exclude unsubmitted applications where goods description, reference or issuing country are null
        exclude_query = Q(dfl_application__imad__submit_datetime__isnull=True) & Q(
            Q(goods_description__isnull=True)
            | Q(deactivated_certificate_reference__isnull=True)
            | Q(issuing_country__isnull=True)
        )

        return (
            cls.objects.select_related("target")
            .prefetch_related("target__files")
            .annotate(
                file_ptr_id=Subquery(sub_query.values("pk")[:1]),
            )
            .exclude(file_ptr_id__isnull=True)
            .exclude(exclude_query)
            .values(*values)
            .iterator(chunk_size=2000)
        )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        # This is a M2M field in V2
        data.pop("dfl_application_id")

        # Remove id and set file_ptr_id because V2 inherits from File model
        data.pop("id")
        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data["id"],
            "dflgoodscertificate_id": data["file_ptr_id"],
            "dflapplication_id": data["dfl_application_id"],
        }

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_id", "target_id"]


class DFLChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", related_name="+"
    )
    certificate_attached = models.CharField(max_length=3, null=True)
    certificate_issued = models.CharField(max_length=3, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["deactivation_certificate_attached"] = data.pop("certificate_attached")
        data["deactivation_certificate_issued"] = data.pop("certificate_issued")

        return data

    @classmethod
    def y_n_fields(cls) -> list[str]:
        return super().y_n_fields() + ["certificate_attached", "certificate_issued"]


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
    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values() + ["goods_certificate_id"]
        sub_query = DFLGoodsCertificate.objects.filter(
            legacy_id=OuterRef("goods_certificate_legacy_id"),
            dfl_application_id=OuterRef("report__supplementary_info__imad__id"),
        )

        return (
            cls.objects.select_related("report__supplementary_info__imad")
            .annotate(
                goods_certificate_id=Subquery(sub_query.values("target__files__pk")[:1]),
            )
            .exclude(goods_certificate_id__isnull=True)
            .values(*values)
            .iterator(chunk_size=2000)
        )
