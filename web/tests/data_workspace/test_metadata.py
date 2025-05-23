from typing import Any

import pytest
from django.urls import reverse

from ._base import BaseTestDataView


class TestMetaDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:metadata")

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result == {
            "tables": [
                {
                    "endpoint": "/data-workspace/v0/cfs-products/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "schedule_id",
                            "type": "Integer",
                        },
                        {
                            "name": "product_name",
                            "type": "String",
                        },
                        {
                            "name": "is_raw_material",
                            "type": "Boolean",
                        },
                        {
                            "name": "product_end_use",
                            "type": "String",
                        },
                        {
                            "name": "product_type_number_list",
                            "type": "ArrayInteger",
                        },
                        {
                            "name": "active_ingredient_list",
                            "type": "ArrayString",
                        },
                        {
                            "name": "cas_number_list",
                            "type": "ArrayString",
                        },
                    ],
                    "indexes": [],
                    "table_name": "cfs-product",
                },
                {
                    "endpoint": "/data-workspace/v0/cfs-schedules/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "export_application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "exporter_status",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "brand_name_holder",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "legislation_ids",
                            "type": "ArrayInteger",
                        },
                        {
                            "name": "biocidal_claim",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "product_eligibility",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "goods_placed_on_uk_market",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "goods_export_only",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "product_standard",
                            "type": "String",
                        },
                        {
                            "name": "any_raw_materials",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "final_product_end_use",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "country_of_manufacture_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "schedule_statements_accordance_with_standards",
                            "type": "Boolean",
                        },
                        {
                            "name": "schedule_statements_is_responsible_person",
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacturer_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_address_entry_type",
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_postcode",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_address",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "created_at",
                            "type": "Datetime",
                        },
                        {
                            "name": "updated_at",
                            "type": "Datetime",
                        },
                        {
                            "name": "is_biocidal",
                            "type": "Boolean",
                        },
                        {
                            "name": "is_biocidal_claim",
                            "type": "Boolean",
                        },
                    ],
                    "indexes": [],
                    "table_name": "cfs-schedule",
                },
                {
                    "endpoint": "/data-workspace/v0/com-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "is_pesticide_on_free_sale_uk",
                            "type": "Boolean",
                        },
                        {
                            "name": "is_manufacturer",
                            "type": "Boolean",
                        },
                        {
                            "name": "product_name",
                            "type": "String",
                        },
                        {
                            "name": "chemical_name",
                            "type": "String",
                        },
                        {
                            "name": "manufacturing_process",
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "com-application",
                },
                {
                    "endpoint": "/data-workspace/v0/export-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "process_type",
                            "type": "String",
                        },
                        {
                            "name": "is_active",
                            "type": "Boolean",
                        },
                        {
                            "name": "created",
                            "type": "Datetime",
                        },
                        {
                            "name": "finished",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "status",
                            "type": "String",
                        },
                        {
                            "name": "applicant_reference",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "application_type_code",
                            "type": "String",
                        },
                        {
                            "name": "contact_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "submit_datetime",
                            "type": "Datetime",
                        },
                        {
                            "name": "last_submit_datetime",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "reassign_datetime",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "reference",
                            "type": "String",
                        },
                        {
                            "name": "decision",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "refuse_reason",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "agent_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "agent_office_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "last_update_datetime",
                            "type": "Datetime",
                        },
                        {
                            "name": "last_updated_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "variation_number",
                            "type": "Integer",
                        },
                        {
                            "name": "created_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "submitted_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "country_names",
                            "type": "ArrayString",
                        },
                        {
                            "name": "exporter_id",
                            "type": "Integer",
                        },
                        {
                            "name": "exporter_office_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                    ],
                    "indexes": [],
                    "table_name": "export-application",
                },
                {
                    "endpoint": "/data-workspace/v0/export-certificate-documents/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "document_pack_id",
                            "type": "Integer",
                        },
                        {
                            "name": "document_pack_status",
                            "type": "String",
                        },
                        {
                            "name": "issue_date",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "document_type",
                            "type": "String",
                        },
                        {
                            "name": "reference",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "country",
                            "nullable": True,
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "export-certificate-document",
                },
                {
                    "table_name": "exporter",
                    "endpoint": "/data-workspace/v0/exporters/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "is_active", "type": "Boolean"},
                        {"name": "name", "type": "String"},
                        {"name": "registered_number", "type": "String", "nullable": True},
                        {"name": "comments", "type": "String", "nullable": True},
                        {"name": "main_exporter_id", "type": "Integer", "nullable": True},
                        {"name": "exclusive_correspondence", "type": "Boolean"},
                    ],
                },
                {
                    "endpoint": "/data-workspace/v0/fa-dfl-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "deactivated_firearm",
                            "type": "Boolean",
                        },
                        {
                            "name": "proof_checked",
                            "type": "Boolean",
                        },
                        {
                            "name": "commodity_code",
                            "type": "String",
                        },
                        {
                            "name": "constabulary_name",
                            "type": "String",
                        },
                        {
                            "name": "know_bought_from",
                            "nullable": True,
                            "type": "Boolean",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-dfl-application",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-dfl-goods/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "goods_description",
                            "type": "String",
                        },
                        {
                            "name": "goods_description_original",
                            "type": "String",
                        },
                        {
                            "name": "deactivated_certificate_reference",
                            "type": "String",
                        },
                        {
                            "name": "issuing_country_name",
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-dfl-goods",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-oil-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "section1",
                            "type": "Boolean",
                        },
                        {
                            "name": "section2",
                            "type": "Boolean",
                        },
                        {
                            "name": "know_bought_from",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "verified_certificates_count",
                            "type": "Integer",
                        },
                        {
                            "name": "user_imported_certificates_count",
                            "type": "Integer",
                        },
                        {
                            "name": "commodity_code",
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-oil-application",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "section1",
                            "type": "Boolean",
                        },
                        {
                            "name": "section2",
                            "type": "Boolean",
                        },
                        {
                            "name": "section5",
                            "type": "Boolean",
                        },
                        {
                            "name": "section58_obsolete",
                            "type": "Boolean",
                        },
                        {
                            "name": "section58_other",
                            "type": "Boolean",
                        },
                        {
                            "name": "section_legacy",
                            "type": "Boolean",
                        },
                        {
                            "name": "other_description",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "military_police",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "eu_single_market",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "manufactured",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "commodity_code",
                            "type": "String",
                        },
                        {
                            "name": "know_bought_from",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "additional_comments",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "verified_section5_count",
                            "type": "Integer",
                        },
                        {
                            "name": "user_section5_count",
                            "type": "Integer",
                        },
                        {
                            "name": "verified_certificates_count",
                            "type": "Integer",
                        },
                        {
                            "name": "user_imported_certificates_count",
                            "type": "Integer",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-application",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section1/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "unlimited_quantity",
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacture",
                            "type": "Boolean",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section1",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section2/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "unlimited_quantity",
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacture",
                            "type": "Boolean",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section2",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section5/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "unlimited_quantity",
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacture",
                            "type": "Boolean",
                        },
                        {
                            "name": "section_5_clause_name",
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section5",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section-legacy/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "unlimited_quantity",
                            "type": "Boolean",
                        },
                        {
                            "name": "obsolete_calibre",
                            "nullable": True,
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section-legacy",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section-obsolete/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "type": "Integer",
                        },
                        {
                            "name": "curiosity_ornament",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "acknowledgement",
                            "type": "Boolean",
                        },
                        {
                            "name": "centrefire",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacture",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "original_chambering",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "obsolete_calibre",
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section-obsolete",
                },
                {
                    "endpoint": "/data-workspace/v0/fa-sil-goods-section-other/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "description",
                            "type": "String",
                        },
                        {
                            "name": "quantity",
                            "type": "Integer",
                        },
                        {
                            "name": "description_original",
                            "type": "String",
                        },
                        {
                            "name": "quantity_original",
                            "type": "Integer",
                        },
                        {
                            "name": "curiosity_ornament",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "acknowledgement",
                            "type": "Boolean",
                        },
                        {
                            "name": "manufacture",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "muzzle_loading",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "rimfire",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "rimfire_details",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "ignition",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "ignition_details",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "ignition_other",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "chamber",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "bore",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "bore_details",
                            "nullable": True,
                            "type": "String",
                        },
                    ],
                    "indexes": [],
                    "table_name": "fa-sil-goods-section-other",
                },
                {
                    "endpoint": "/data-workspace/v0/gmp-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "brand_name",
                            "type": "String",
                        },
                        {
                            "name": "is_responsible_person",
                            "type": "String",
                        },
                        {
                            "name": "responsible_person_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "responsible_person_address_entry_type",
                            "type": "String",
                        },
                        {
                            "name": "responsible_person_postcode",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "responsible_person_address",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "responsible_person_country",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "is_manufacturer",
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_address_entry_type",
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_postcode",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_address",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "manufacturer_country",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "gmp_certificate_issued",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "auditor_accredited",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "auditor_certified",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "supporting_documents_types",
                            "type": "ArrayString",
                        },
                    ],
                    "indexes": [],
                    "table_name": "gmp-application",
                },
                {
                    "endpoint": "/data-workspace/v0/import-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "process_type",
                            "type": "String",
                        },
                        {
                            "name": "is_active",
                            "type": "Boolean",
                        },
                        {
                            "name": "created",
                            "type": "Datetime",
                        },
                        {
                            "name": "finished",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "status",
                            "type": "String",
                        },
                        {
                            "name": "applicant_reference",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "application_type_code",
                            "type": "String",
                        },
                        {
                            "name": "contact_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "submit_datetime",
                            "type": "Datetime",
                        },
                        {
                            "name": "last_submit_datetime",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "reassign_datetime",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "reference",
                            "type": "String",
                        },
                        {
                            "name": "decision",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "refuse_reason",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "agent_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "agent_office_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "last_update_datetime",
                            "type": "Datetime",
                        },
                        {
                            "name": "last_updated_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "variation_number",
                            "type": "Integer",
                        },
                        {
                            "name": "created_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "submitted_by_id",
                            "type": "Integer",
                        },
                        {
                            "name": "application_sub_type",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "importer_id",
                            "type": "Integer",
                        },
                        {
                            "name": "importer_office_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "legacy_case_flag",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "chief_usage_status",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "variation_decision",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "variation_refuse_reason",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "origin_country_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "consignment_country_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "commodity_group_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "cover_letter_text",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "imi_submitted_by_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                        {
                            "name": "imi_submit_datetime",
                            "nullable": True,
                            "type": "Datetime",
                        },
                    ],
                    "indexes": [],
                    "table_name": "import-application",
                },
                {
                    "endpoint": "/data-workspace/v0/import-licence-documents/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "document_pack_id",
                            "type": "Integer",
                        },
                        {
                            "name": "document_pack_status",
                            "type": "String",
                        },
                        {
                            "name": "issue_date",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "document_type",
                            "type": "String",
                        },
                        {
                            "name": "reference",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "issue_paper_licence_only",
                            "nullable": True,
                            "type": "Boolean",
                        },
                        {
                            "name": "licence_start_date",
                            "nullable": True,
                            "type": "Date",
                        },
                        {
                            "name": "licence_end_date",
                            "nullable": True,
                            "type": "Date",
                        },
                    ],
                    "indexes": [],
                    "table_name": "import-licence-document",
                },
                {
                    "table_name": "importer",
                    "endpoint": "/data-workspace/v0/importers/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "is_active", "type": "Boolean"},
                        {"name": "type", "type": "String"},
                        {"name": "name", "type": "String", "nullable": True},
                        {"name": "registered_number", "type": "String", "nullable": True},
                        {"name": "eori_number", "type": "String", "nullable": True},
                        {"name": "region_origin", "type": "String", "nullable": True},
                        {"name": "user_id", "type": "Integer", "nullable": True},
                        {"name": "comments", "type": "String", "nullable": True},
                        {"name": "main_importer_id", "type": "Integer", "nullable": True},
                    ],
                },
                {
                    "endpoint": "/data-workspace/v0/legislations/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "name",
                            "type": "String",
                        },
                        {
                            "name": "is_active",
                            "type": "Boolean",
                        },
                        {
                            "name": "is_biocidal",
                            "type": "Boolean",
                        },
                        {
                            "name": "is_eu_cosmetics_regulation",
                            "type": "Boolean",
                        },
                        {
                            "name": "is_biocidal_claim",
                            "type": "Boolean",
                        },
                        {
                            "name": "gb_legislation",
                            "type": "Boolean",
                        },
                        {
                            "name": "ni_legislation",
                            "type": "Boolean",
                        },
                    ],
                    "indexes": [],
                    "table_name": "legislation",
                },
                {
                    "endpoint": "/data-workspace/v0/nuclear-material-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "nature_of_business",
                            "type": "String",
                        },
                        {
                            "name": "consignor_name",
                            "type": "String",
                        },
                        {
                            "name": "consignor_address",
                            "type": "String",
                        },
                        {
                            "name": "end_user_name",
                            "type": "String",
                        },
                        {
                            "name": "end_user_address",
                            "type": "String",
                        },
                        {
                            "name": "intended_use_of_shipment",
                            "type": "String",
                        },
                        {
                            "name": "shipment_start_date",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "shipment_end_date",
                            "nullable": True,
                            "type": "Datetime",
                        },
                        {
                            "name": "security_team_contact_information",
                            "type": "String",
                        },
                        {
                            "name": "licence_type",
                            "type": "String",
                        },
                        {
                            "name": "supporting_documents_count",
                            "type": "Integer",
                        },
                    ],
                    "indexes": [],
                    "table_name": "nuclear-material-application",
                },
                {
                    "endpoint": "/data-workspace/v0/nuclear-material-goods/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "commodity_code",
                            "type": "String",
                        },
                        {
                            "name": "goods_description",
                            "type": "String",
                        },
                        {
                            "asdecimal": True,
                            "name": "quantity_amount",
                            "nullable": True,
                            "type": "Float",
                        },
                        {
                            "name": "unit",
                            "type": "String",
                        },
                        {
                            "name": "unlimited_quantity",
                            "type": "Boolean",
                        },
                        {
                            "name": "goods_description_original",
                            "type": "String",
                        },
                        {
                            "asdecimal": True,
                            "name": "quantity_amount_original",
                            "nullable": True,
                            "type": "Float",
                        },
                    ],
                    "indexes": [],
                    "table_name": "nuclear-material-goods",
                },
                {
                    "table_name": "office",
                    "endpoint": "/data-workspace/v0/offices/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "is_active", "type": "Boolean"},
                        {"name": "address_1", "type": "String"},
                        {"name": "address_2", "type": "String", "nullable": True},
                        {"name": "address_3", "type": "String", "nullable": True},
                        {"name": "address_4", "type": "String", "nullable": True},
                        {"name": "address_5", "type": "String", "nullable": True},
                        {"name": "postcode", "type": "String", "nullable": True},
                        {"name": "eori_number", "type": "String", "nullable": True},
                        {"name": "address_entry_type", "type": "String"},
                        {"name": "importer_id", "type": "Integer", "nullable": True},
                        {"name": "exporter_id", "type": "Integer", "nullable": True},
                    ],
                },
                {
                    "endpoint": "/data-workspace/v0/sanctions-applications/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "exporter_name",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "exporter_address",
                            "nullable": True,
                            "type": "String",
                        },
                        {
                            "name": "supporting_documents_count",
                            "type": "Integer",
                        },
                    ],
                    "indexes": [],
                    "table_name": "sanctions-application",
                },
                {
                    "endpoint": "/data-workspace/v0/sanctions-goods/",
                    "fields": [
                        {
                            "name": "id",
                            "primary_key": True,
                            "type": "Integer",
                        },
                        {
                            "name": "application_id",
                            "type": "Integer",
                        },
                        {
                            "name": "commodity_code",
                            "type": "String",
                        },
                        {
                            "name": "goods_description",
                            "type": "String",
                        },
                        {
                            "asdecimal": True,
                            "name": "quantity_amount",
                            "type": "Float",
                        },
                        {
                            "asdecimal": True,
                            "name": "value",
                            "type": "Float",
                        },
                        {
                            "name": "goods_description_original",
                            "type": "String",
                        },
                        {
                            "asdecimal": True,
                            "name": "quantity_amount_original",
                            "type": "Float",
                        },
                        {
                            "asdecimal": True,
                            "name": "value_original",
                            "type": "Float",
                        },
                    ],
                    "indexes": [],
                    "table_name": "sanctions-goods",
                },
                {
                    "table_name": "user-feedback-survey",
                    "endpoint": "/data-workspace/v0/user-surveys/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "satisfaction", "type": "String"},
                        {"name": "issues", "type": "ArrayString"},
                        {"name": "issue_details", "type": "String"},
                        {"name": "find_service", "type": "String"},
                        {"name": "find_service_details", "type": "String"},
                        {"name": "additional_support", "type": "String"},
                        {"name": "service_improvements", "type": "String"},
                        {"name": "future_contact", "type": "String"},
                        {"name": "referrer_path", "type": "String"},
                        {"name": "site", "type": "String"},
                        {"name": "application_id", "type": "Integer", "nullable": True},
                        {"name": "created_by_id", "type": "Integer"},
                        {"name": "created_datetime", "type": "Datetime"},
                    ],
                },
                {
                    "table_name": "user",
                    "endpoint": "/data-workspace/v0/users/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "title", "type": "String", "nullable": True},
                        {"name": "first_name", "type": "String"},
                        {"name": "last_name", "type": "String"},
                        {"name": "email", "type": "String"},
                        {"name": "primary_email_address", "type": "String", "nullable": True},
                        {"name": "organisation", "type": "String", "nullable": True},
                        {"name": "department", "type": "String", "nullable": True},
                        {"name": "job_title", "type": "String", "nullable": True},
                        {"name": "date_joined", "type": "Datetime", "nullable": True},
                        {"name": "last_login", "type": "Datetime", "nullable": True},
                        {"name": "exporter_ids", "type": "ArrayInteger"},
                        {"name": "importer_ids", "type": "ArrayInteger"},
                        {"name": "group_names", "type": "ArrayString"},
                    ],
                },
                {
                    "table_name": "variation-request",
                    "endpoint": "/data-workspace/v0/variation-requests/",
                    "indexes": [],
                    "fields": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "application_id", "type": "Integer"},
                        {"name": "status", "type": "String"},
                        {"name": "extension_flag", "type": "Boolean"},
                        {"name": "requested_datetime", "type": "Datetime"},
                        {"name": "requested_by_id", "type": "Integer"},
                        {"name": "what_varied", "type": "String"},
                        {"name": "why_varied", "type": "String", "nullable": True},
                        {"name": "when_varied", "type": "Date", "nullable": True},
                        {"name": "reject_cancellation_reason", "type": "String", "nullable": True},
                        {"name": "update_request_reason", "type": "String", "nullable": True},
                        {"name": "closed_datetime", "type": "Datetime", "nullable": True},
                        {"name": "closed_by_id", "type": "Integer", "nullable": True},
                    ],
                },
            ]
        }
