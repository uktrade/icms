import datetime as dt
from decimal import Decimal

from .base import ApplicationBaseSerializer, BaseResultsSerializer, BaseSerializer
from .case import CaseDocumentSerializer


class ImportApplicationSerializer(ApplicationBaseSerializer):
    application_sub_type: str | None
    importer_id: int
    importer_office_id: int | None
    legacy_case_flag: bool | None
    chief_usage_status: str | None
    variation_decision: str | None
    variation_refuse_reason: str | None
    origin_country_name: str | None
    consignment_country_name: str | None
    commodity_group_id: int | None
    cover_letter_text: str | None
    imi_submitted_by_id: int | None
    imi_submit_datetime: dt.datetime | None


class ImportApplicationListSerializer(BaseResultsSerializer):
    results: list[ImportApplicationSerializer]


class ImportLicenceDocumentSerializer(CaseDocumentSerializer):
    issue_paper_licence_only: bool | None
    licence_start_date: dt.date | None
    licence_end_date: dt.date | None


class ImportLicenceDocumentListSerializer(BaseResultsSerializer):
    results: list[CaseDocumentSerializer]


class NuclearMaterialApplicationSerializer(BaseSerializer):
    nature_of_business: str
    consignor_name: str
    consignor_address: str
    end_user_name: str
    end_user_address: str
    intended_use_of_shipment: str
    shipment_start_date: dt.datetime | None
    shipment_end_date: dt.datetime | None
    security_team_contact_information: str
    licence_type: str
    supporting_documents_count: int


class NuclearMaterialApplicationListSerializer(BaseResultsSerializer):
    results: list[NuclearMaterialApplicationSerializer]


class NuclearMaterialGoodsSerializer(BaseSerializer):
    application_id: int
    commodity_code: str
    goods_description: str
    quantity_amount: Decimal | None
    unit: str
    unlimited_quantity: bool
    goods_description_original: str
    quantity_amount_original: Decimal | None


class NuclearMaterialGoodsListSerializer(BaseResultsSerializer):
    results: list[NuclearMaterialGoodsSerializer]


class SanctionsApplicationSerializer(BaseSerializer):
    exporter_name: str | None
    exporter_address: str | None
    supporting_documents_count: int


class SanctionsApplicationListSerializer(BaseResultsSerializer):
    results: list[SanctionsApplicationSerializer]


class SanctionsGoodsSerializer(BaseSerializer):
    application_id: int
    commodity_code: str
    goods_description: str
    quantity_amount: Decimal
    value: Decimal
    goods_description_original: str
    quantity_amount_original: Decimal
    value_original: Decimal


class SanctionsGoodsListSerializer(BaseResultsSerializer):
    results: list[SanctionsGoodsSerializer]
