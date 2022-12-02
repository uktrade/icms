from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileM2MBase
from data_migration.models.reference import Commodity, CommodityGroup, Country
from data_migration.utils.format import validate_decimal

from .import_application import ChecklistBase, ImportApplication, ImportApplicationBase


class OutwardProcessingTradeApplication(ImportApplicationBase):
    imad = models.ForeignKey(ImportApplication, on_delete=models.CASCADE, to_field="imad_id")
    customs_office_name = models.CharField(max_length=100, null=True)
    customs_office_address = models.TextField(max_length=4000, null=True)
    rate_of_yield = models.CharField(max_length=20, null=True)
    rate_of_yield_calc_method = models.TextField(max_length=4000, null=True)
    last_export_day = models.DateField(null=True)
    reimport_period = models.CharField(max_length=20, null=True)
    nature_process_ops = models.TextField(max_length=4000, null=True)
    suggested_id = models.TextField(max_length=4000, null=True)
    cp_origin_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    cp_processing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.CASCADE, null=True)
    cp_total_quantity = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    cp_total_value = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    cp_commodities_xml = models.TextField(null=True)
    teg_origin_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )
    teg_total_quantity = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
    )
    teg_total_value = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    teg_goods_description = models.CharField(null=True, max_length=4096)
    teg_commodities_xml = models.TextField(null=True)
    fq_similar_to_own_factory = models.CharField(max_length=3, null=True)
    fq_manufacturing_within_eu = models.CharField(max_length=3, null=True)
    fq_maintained_in_eu = models.CharField(max_length=3, null=True)
    fq_maintained_in_eu_r = models.CharField(max_length=4000, null=True)
    fq_employment_decreased = models.CharField(max_length=3, null=True)
    fq_employment_decreased_r = models.CharField(max_length=4000, null=True)
    fq_prior_authorisation = models.CharField(max_length=3, null=True)
    fq_prior_authorisation_r = models.CharField(max_length=4000, null=True)
    fq_past_beneficiary = models.CharField(max_length=3, null=True)
    fq_past_beneficiary_r = models.CharField(max_length=4000, null=True)
    fq_new_application = models.CharField(max_length=3, null=True)
    fq_new_application_reasons = models.CharField(max_length=4000, null=True)
    fq_further_authorisation = models.CharField(max_length=3, null=True)
    fq_further_auth_reasons = models.CharField(max_length=4000, null=True)
    fq_subcontract_production = models.CharField(max_length=3, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        validate_decimal(["rate_of_yield", "reimport_period"], data)

        return data

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "fq_employment_decreased_reasons": F("fq_employment_decreased_r"),
            "fq_maintained_in_eu_reasons": F("fq_maintained_in_eu_r"),
            "fq_prior_authorisation_reasons": F("fq_prior_authorisation_r"),
            "fq_past_beneficiary_reasons": F("fq_past_beneficiary_r"),
            "fq_further_authorisation_reasons": F("fq_further_auth_reasons"),
            "cp_category": F("commodity_group__group_code"),
            "cp_category_licence_description": F("commodity_group__group_description"),
        }

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "commodity_group_id",
            "fq_employment_decreased_r",
            "fq_maintained_in_eu_r",
            "fq_prior_authorisation_r",
            "fq_past_beneficiary_r",
            "fq_further_auth_reasons",
        ]


class OutwardProcessingTradeFile(FileM2MBase):
    TARGET_TYPES: dict[str, str] = {
        "IMP_OPT_FURTHER_AUTH_DOC": "fq_further_authorisation",
        "IMP_OPT_PRIOR_AUTH_DOC": "fq_prior_authorisation",
        "IMP_SUPPORTING_DOC": "supporting_document",
        "IMP_OPT_BENEFICIARY_DOC": "fq_past_beneficiary",
        "IMP_OPT_EMPLOY_DOC": "fq_employment_decreased",
        "FQ_NEW_APPLICATION": "fq_new_application",
        "IMP_OPT_NEW_APP_JUST_DOC": "fq_new_application",
        "IMP_OPT_SUBCONTRACT_DOC": "fq_subcontract_production",
    }
    TARGET_TYPE = list(TARGET_TYPES.keys())
    FILE_MODEL = "outwardprocessingtradefile"
    APP_MODEL = "outwardprocessingtradeapplication"

    class Meta:
        abstract = True

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            File.objects.filter(
                target__target_type__in=cls.TARGET_TYPE,
                target__folder__folder_type="IMP_APP_DOCUMENTS",
                target__folder__app_model=cls.APP_MODEL,
            )
            .values(file_ptr_id=F("pk"), target_type=F("target__target_type"))
            .iterator(chunk_size=2000)
        )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["file_type"] = cls.TARGET_TYPES[data.pop("target_type")]
        return data


class OPTTegCommodity(MigrationBase):
    outwardprocessingtradeapplication = models.ForeignKey(
        OutwardProcessingTradeApplication, on_delete=models.CASCADE
    )
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)


class OPTCpCommodity(MigrationBase):
    outwardprocessingtradeapplication = models.ForeignKey(
        OutwardProcessingTradeApplication, on_delete=models.CASCADE
    )
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)


class OPTChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="+", to_field="imad_id"
    )
    endorsements_listed = None
    operator_requests_submitted = models.CharField(max_length=3, null=True)
    authority_to_issue = models.CharField(max_length=3, null=True)

    @classmethod
    def y_n_fields(cls) -> list[str]:
        y_n_fields = super().y_n_fields() + ["operator_requests_submitted", "authority_to_issue"]
        y_n_fields.remove("endorsements_listed")

        return y_n_fields
