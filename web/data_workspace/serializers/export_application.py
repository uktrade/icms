import datetime as dt

from django.urls import reverse

from .base import ApplicationBaseSerializer, BaseResultsSerializer, BaseSerializer
from .case import CaseDocumentSerializer


class ExportApplicationSerializer(ApplicationBaseSerializer):
    country_names: list[str]
    exporter_id: int
    exporter_office_id: int | None


class ExportApplicationListSerializer(BaseResultsSerializer):
    results: list[ExportApplicationSerializer]


class ExportCertificateDocumentSerializer(CaseDocumentSerializer):
    application_id: int
    document_pack_id: int
    document_pack_status: str
    issue_date: dt.datetime | None
    document_type: str
    reference: str | None
    country: str | None


class ExportDocumentListSerializer(BaseResultsSerializer):
    results: list[ExportCertificateDocumentSerializer]


class GMPApplicationSerializer(BaseSerializer):
    brand_name: str
    is_responsible_person: str
    responsible_person_name: str | None
    responsible_person_address_entry_type: str
    responsible_person_postcode: str | None
    responsible_person_address: str | None
    responsible_person_country: str | None
    is_manufacturer: str
    manufacturer_name: str | None
    manufacturer_address_entry_type: str
    manufacturer_postcode: str | None
    manufacturer_address: str | None
    manufacturer_country: str | None
    gmp_certificate_issued: str | None
    auditor_accredited: str | None
    auditor_certified: str | None
    supporting_documents_types: list[str]

    @classmethod
    def url(cls) -> str:
        return reverse("data-workspace:gmp-application-data", kwargs={"version": "v0"})


class GMPApplicationListSerializer(BaseResultsSerializer):
    results: list[GMPApplicationSerializer]


class COMApplicationSerializer(BaseSerializer):
    is_pesticide_on_free_sale_uk: bool
    is_manufacturer: bool
    product_name: str
    chemical_name: str
    manufacturing_process: str

    @classmethod
    def url(cls) -> str:
        return reverse("data-workspace:com-application-data", kwargs={"version": "v0"})


class COMApplicationListSerializer(BaseResultsSerializer):
    results: list[COMApplicationSerializer]


class CFSScheduleSerializer(BaseSerializer):
    export_application_id: int
    exporter_status: str | None
    brand_name_holder: str | None
    legislation_ids: list[int]
    biocidal_claim: str | None
    product_eligibility: str | None
    goods_placed_on_uk_market: str | None
    goods_export_only: str | None
    product_standard: str
    any_raw_materials: str | None
    final_product_end_use: str | None
    country_of_manufacture_name: str | None
    schedule_statements_accordance_with_standards: bool
    schedule_statements_is_responsible_person: bool
    manufacturer_name: str | None
    manufacturer_address_entry_type: str
    manufacturer_postcode: str | None
    manufacturer_address: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    is_biocidal: bool
    is_biocidal_claim: bool

    @classmethod
    def url(cls) -> str:
        return reverse("data-workspace:cfs-schedule-data", kwargs={"version": "v0"})


class CFSScheduleListSerializer(BaseResultsSerializer):
    results: list[CFSScheduleSerializer]


class CFSProductSerializer(BaseSerializer):
    schedule_id: int
    product_name: str
    is_raw_material: bool
    product_end_use: str
    product_type_number_list: list[int]
    active_ingredient_list: list[str]
    cas_number_list: list[str]

    @classmethod
    def url(cls) -> str:
        return reverse("data-workspace:cfs-product-data", kwargs={"version": "v0"})


class CFSProductListSerializer(BaseResultsSerializer):
    results: list[CFSProductSerializer]


class LegislationSerializer(BaseSerializer):
    name: str
    is_active: bool
    is_biocidal: bool
    is_eu_cosmetics_regulation: bool
    is_biocidal_claim: bool
    gb_legislation: bool
    ni_legislation: bool


class LegislationListSerializer(BaseResultsSerializer):
    results: list[LegislationSerializer]
