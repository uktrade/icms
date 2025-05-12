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
                    "endpoint": "/data-workspace/v0/case-documents/",
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
                    "table_name": "casedocument",
                },
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
                    "table_name": "cfsproduct",
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
                    "table_name": "cfsschedule",
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
                    "table_name": "comapplication",
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
                            "name": "applicant_reference",
                            "type": "String",
                        },
                        {
                            "name": "application_type_code",
                            "type": "String",
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
                        {
                            "name": "contact_id",
                            "nullable": True,
                            "type": "Integer",
                        },
                    ],
                    "indexes": [],
                    "table_name": "exportapplication",
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
                    "table_name": "gmpapplication",
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
                    "table_name": "userfeedbacksurvey",
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
            ]
        }
