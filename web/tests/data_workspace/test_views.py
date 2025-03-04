import json
from http import HTTPStatus
from typing import Any

import pytest
from django.urls import reverse

from web.models import UserFeedbackSurvey
from web.tests.api_auth import JSON_TYPE, make_testing_hawk_sender


def at_example(prefix: str) -> str:
    return f"{prefix}@example.com"  # /PS-IGNORE


DT_STRING = "%Y-%m-%dT%H:%M:%S.%fZ"


class BaseTestDataView:
    def test_authentication_failure(self):
        content = json.dumps({})
        response = self.client.post(
            self.url,
            content,
            content_type=JSON_TYPE,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_authentication_failure_hmrc_creds(self):
        content = json.dumps({})
        sender = make_testing_hawk_sender(
            "POST", self.url, api_type="hmrc", content=content, content_type=JSON_TYPE
        )
        response = self.client.post(
            self.url,
            content,
            content_type=JSON_TYPE,
            HTTP_HAWK_AUTHENTICATION=sender.request_header,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_authetication(self):
        content = json.dumps({})
        sender = make_testing_hawk_sender(
            "POST", self.url, api_type="data_workspace", content=content, content_type=JSON_TYPE
        )
        response = self.client.post(
            self.url,
            content,
            content_type=JSON_TYPE,
            HTTP_HAWK_AUTHENTICATION=sender.request_header,
        )
        assert response.status_code == HTTPStatus.OK
        result = response.json()
        self.check_result(result)

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert True


class TestMetaDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:metadata")

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result == [
            {
                "endpoint": "/data-workspace/v0/users/",
                "fields": [
                    {
                        "name": "id",
                        "primary_key": True,
                        "type": "Integer",
                    },
                    {
                        "name": "title",
                        "nullable": True,
                        "type": "String",
                    },
                    {
                        "name": "first_name",
                        "type": "String",
                    },
                    {
                        "name": "last_name",
                        "type": "String",
                    },
                    {
                        "name": "email",
                        "type": "String",
                    },
                    {
                        "name": "primary_email_address",
                        "nullable": True,
                        "type": "String",
                    },
                    {
                        "name": "organisation",
                        "nullable": True,
                        "type": "String",
                    },
                    {
                        "name": "department",
                        "nullable": True,
                        "type": "String",
                    },
                    {
                        "name": "job_title",
                        "nullable": True,
                        "type": "String",
                    },
                    {
                        "name": "date_joined",
                        "nullable": True,
                        "type": "Datetime",
                    },
                    {
                        "name": "last_login",
                        "nullable": True,
                        "type": "Datetime",
                    },
                    {
                        "name": "exporter_ids",
                        "type": "ArrayInteger",
                    },
                    {
                        "name": "importer_ids",
                        "type": "ArrayInteger",
                    },
                    {
                        "name": "group_names",
                        "type": "ArrayString",
                    },
                ],
                "indexes": [],
                "table_name": "icms_user",
            },
            {
                "endpoint": "/data-workspace/v0/user-surveys/",
                "fields": [
                    {
                        "name": "id",
                        "primary_key": True,
                        "type": "Integer",
                    },
                    {
                        "name": "satisfaction",
                        "type": "String",
                    },
                    {
                        "name": "issues",
                        "type": "ArrayString",
                    },
                    {
                        "name": "issue_details",
                        "type": "String",
                    },
                    {
                        "name": "find_service",
                        "type": "String",
                    },
                    {
                        "name": "find_service_details",
                        "type": "String",
                    },
                    {
                        "name": "additional_support",
                        "type": "String",
                    },
                    {
                        "name": "service_improvements",
                        "type": "String",
                    },
                    {
                        "name": "future_contact",
                        "type": "String",
                    },
                    {
                        "name": "referrer_path",
                        "type": "String",
                    },
                    {
                        "name": "site",
                        "type": "String",
                    },
                    {
                        "name": "process_id",
                        "nullable": True,
                        "type": "Integer",
                    },
                    {
                        "name": "created_by_id",
                        "type": "Integer",
                    },
                    {
                        "name": "created_datetime",
                        "type": "Datetime",
                    },
                ],
                "indexes": [],
                "table_name": "icms_userfeedbacksurvey",
            },
        ]


class TestUserDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:user-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        users = result
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
            "date_joined": "2024-01-20T00:00:00Z",
            "last_login": None,
            "exporter_ids": [],
            "importer_ids": [],
            "group_names": [],
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


class TestUserFeedbackSurveyDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_submitted, exporter_one_contact):
        self.client = cw_client
        self.url = reverse("data-workspace:user-survey-data", kwargs={"version": "v0"})
        self.app = cfs_app_submitted
        self.user = exporter_one_contact
        self.survey = UserFeedbackSurvey.objects.create(
            satisfaction=UserFeedbackSurvey.SatisfactionLevel.SATISFIED,
            issues=[
                UserFeedbackSurvey.IssuesChoices.LACKS_FEATURE,
                UserFeedbackSurvey.IssuesChoices.OTHER,
            ],
            issue_details="some other issue",
            find_service=UserFeedbackSurvey.EaseFindChoices.EASY,
            find_service_details="",
            service_improvements="test",
            future_contact="yes",
            referrer_path="/submit",
            site="exporter",
            process_id=self.app.pk,
            created_by=self.user,
        )

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert len(result) == 1
        assert result[0] == {
            "id": self.survey.id,
            "satisfaction": self.survey.satisfaction,
            "issues": self.survey.issues,
            "issue_details": "some other issue",
            "find_service": self.survey.find_service,
            "find_service_details": "",
            "service_improvements": "test",
            "additional_support": "",
            "future_contact": "yes",
            "referrer_path": "/submit",
            "site": "exporter",
            "process_id": self.app.pk,
            "created_by_id": self.user.pk,
            "created_datetime": self.survey.created_datetime.strftime(DT_STRING),
        }
