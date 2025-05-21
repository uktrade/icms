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


class FaDflApplicationSerializer(BaseSerializer):
    deactivated_firearm: bool
    proof_checked: bool
    commodity_code: str
    constabulary_name: str
    know_bought_from: bool | None


class FaDflApplicationListSerializer(BaseResultsSerializer):
    results: list[FaDflApplicationSerializer]


class FaDflGoodsSerializer(BaseSerializer):
    application_id: int
    goods_description: str
    goods_description_original: str
    deactivated_certificate_reference: str
    issuing_country_name: str


class FaDflGoodsListSerializer(BaseResultsSerializer):
    results: list[FaDflGoodsSerializer]


class FaOilApplicationSerializer(BaseSerializer):
    section1: bool
    section2: bool
    know_bought_from: bool | None
    verified_certificates_count: int
    user_imported_certificates_count: int
    commodity_code: str


class FaOilApplicationListSerializer(BaseResultsSerializer):
    results: list[FaOilApplicationSerializer]


class FaSilApplicationSerializer(BaseSerializer):
    section1: bool
    section2: bool
    section5: bool
    section58_obsolete: bool
    section58_other: bool
    section_legacy: bool
    other_description: str | None
    military_police: bool | None
    eu_single_market: bool | None
    manufactured: bool | None
    commodity_code: str
    know_bought_from: bool | None
    additional_comments: str | None
    verified_section5_count: int
    user_section5_count: int
    verified_certificates_count: int
    user_imported_certificates_count: int


class FaSilApplicationListSerializer(BaseResultsSerializer):
    results: list[FaSilApplicationSerializer]


class FaSilGoodsBaseSerializer(BaseSerializer):
    application_id: int
    description: str
    quantity: int | None
    description_original: str
    quantity_original: int | None
    unlimited_quantity: bool


class FaSilGoodsSection1Serializer(FaSilGoodsBaseSerializer):
    manufacture: bool


class FaSilGoodsSection1ListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSection1Serializer]


class FaSilGoodsSection2Serializer(FaSilGoodsBaseSerializer):
    manufacture: bool


class FaSilGoodsSection2ListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSection2Serializer]


class FaSilGoodsSection5Serializer(FaSilGoodsBaseSerializer):
    manufacture: bool
    section_5_clause_name: str


class FaSilGoodsSection5ListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSection5Serializer]


class FaSilGoodsSectionObsoleteSerializer(BaseSerializer):
    application_id: int
    description: str
    quantity: int
    description_original: str
    quantity_original: int
    curiosity_ornament: bool | None
    acknowledgement: bool
    centrefire: bool | None
    manufacture: bool | None
    original_chambering: bool | None
    obsolete_calibre: str


class FaSilGoodsSectionObsoleteListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSectionObsoleteSerializer]


class FaSilGoodsSectionOtherSerializer(BaseSerializer):
    application_id: int
    description: str
    quantity: int
    description_original: str
    quantity_original: int
    curiosity_ornament: bool | None
    acknowledgement: bool
    manufacture: bool | None
    muzzle_loading: bool | None
    rimfire: bool | None
    rimfire_details: str | None
    ignition: bool | None
    ignition_details: str | None
    ignition_other: str | None
    chamber: bool | None
    bore: bool | None
    bore_details: str | None


class FaSilGoodsSectionOtherListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSectionOtherSerializer]


class FaSilGoodsSectionLegacySerializer(FaSilGoodsBaseSerializer):
    obsolete_calibre: str | None


class FaSilGoodsSectionLegacyListSerializer(BaseResultsSerializer):
    results: list[FaSilGoodsSectionLegacySerializer]


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
