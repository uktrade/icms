from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.reference import Commodity, CommodityGroup, Country

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
