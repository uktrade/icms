from typing import Any

from django.db import models

from data_migration.models.file import FileM2MBase
from data_migration.models.reference import Commodity
from data_migration.utils.format import validate_decimal

from .import_application import ChecklistBase, ImportApplication, ImportApplicationBase


class DerogationsApplication(ImportApplicationBase):
    imad = models.ForeignKey(ImportApplication, on_delete=models.CASCADE, to_field="imad_id")
    contract_sign_date = models.DateField(null=True)
    contract_completion_date = models.DateField(null=True)
    explanation = models.CharField(max_length=4096, null=True)
    commodity = models.ForeignKey(Commodity, on_delete=models.PROTECT, null=True, related_name="+")
    goods_description = models.CharField(max_length=4096, null=True)
    quantity = models.CharField(max_length=40, null=True)
    unit = models.CharField(max_length=40, null=True)
    value = models.CharField(max_length=40, null=True)
    entity_consulted_name = models.CharField(max_length=500, null=True)
    activity_benefit_anyone = models.CharField(max_length=3, null=True)
    purpose_of_request = models.CharField(max_length=3, null=True)
    civilian_purpose_details = models.CharField(max_length=4096, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        validate_decimal(["quantity", "value"], data)

        return data


class DerogationsChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )
    supporting_document_received = models.CharField(max_length=3, null=True)
    sncorf_consulted = models.CharField(max_length=3, null=True)
    sncorf_response_within_30_days = models.CharField(max_length=3, null=True)
    beneficiaries_not_on_list = models.CharField(max_length=3, null=True)
    request_purpose_confirmed = models.CharField(max_length=3, null=True)

    @classmethod
    def y_n_fields(cls) -> list[str]:
        return super().y_n_fields() + [
            "supporting_document_received",
            "sncorf_consulted",
            "sncorf_response_within_30_days",
            "beneficiaries_not_on_list",
            "request_purpose_confirmed",
        ]


class DerogationsSupportingDoc(FileM2MBase):
    APP_MODEL = "derogationsapplication"

    class Meta:
        abstract = True
