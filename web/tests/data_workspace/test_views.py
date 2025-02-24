import json
from http import HTTPStatus

import pytest
from django.urls import reverse

from web.tests.api_auth import JSON_TYPE, make_testing_hawk_sender


def at_example(prefix: str) -> str:
    return f"{prefix}@example.com"  # /PS-IGNORE


class TestUserDataView:
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:user-data", kwargs={"version": "v0"})

    def test_authentication_failure(self):
        content = json.dumps({})
        response = self.client.post(
            self.url,
            content,
            content_type=JSON_TYPE,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_authetication(self):
        content = json.dumps({})
        sender = make_testing_hawk_sender("POST", self.url, content=content, content_type=JSON_TYPE)
        response = self.client.post(
            self.url,
            content,
            content_type=JSON_TYPE,
            HTTP_HAWK_AUTHENTICATION=sender.request_header,
        )
        assert response.status_code == HTTPStatus.OK

        result = response.json()
        users = result["users"]
        email = at_example("access_request_user")

        assert len(users) == 22
        assert users[0] == {
            "id": 1,
            "title": None,
            "first_name": "access_request_user_first_name",
            "last_name": "access_request_user_last_name",
            "email": email,
            "primary_email_address": email,
            "department": "access_request_user_dep",
            "job_title": "access_request_user_job_title",
            "organisation": "access_request_user_org",
            "date_joined": "2024-01-20T00:00:00Z",  # /PS-IGNORE
            "last_login": None,
            "exporter_ids": [],
            "importer_ids": [],
            "group_names": [None],
        }

        email = at_example("I1_main_contact")
        assert users[1] == {
            "id": 2,
            "title": None,
            "first_name": "I1_main_contact_first_name",
            "last_name": "I1_main_contact_last_name",
            "email": email,
            "primary_email_address": email,
            "organisation": "I1_main_contact_org",
            "department": "I1_main_contact_dep",
            "job_title": "I1_main_contact_job_title",
            "date_joined": "2024-01-20T00:00:00Z",
            "last_login": None,
            "exporter_ids": [],
            "importer_ids": [1],
            "group_names": ["Importer User"],
        }

        email = at_example("E1_inactive_contact")
        assert users[8] == {
            "id": 9,
            "title": None,
            "first_name": "E1_inactive_contact_first_name",
            "last_name": "E1_inactive_contact_last_name",
            "email": email,
            "primary_email_address": email,
            "organisation": "E1_inactive_contact_org",
            "department": "E1_inactive_contact_dep",
            "job_title": "E1_inactive_contact_job_title",
            "date_joined": "2024-01-20T00:00:00Z",
            "last_login": None,
            "exporter_ids": [1],
            "importer_ids": [],
            "group_names": ["Exporter User"],
        }

        email = at_example("prototype_user")
        assert users[-1] == {
            "id": 22,
            "title": None,
            "first_name": "prototype_user_first_name",
            "last_name": "prototype_user_last_name",
            "email": email,
            "primary_email_address": email,
            "department": "prototype_user_dep",
            "job_title": "prototype_user_job_title",
            "organisation": "prototype_user_org",
            "date_joined": "2024-01-20T00:00:00Z",  # /PS-IGNORE
            "last_login": None,
            "exporter_ids": [],
            "importer_ids": [],
            "group_names": ["ECIL Prototype User"],
        }
