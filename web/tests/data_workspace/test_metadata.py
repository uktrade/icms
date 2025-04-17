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
                        {"name": "process_id", "type": "Integer", "nullable": True},
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
