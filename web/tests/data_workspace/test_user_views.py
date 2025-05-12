from typing import Any

import pytest
from django.urls import reverse

from web.models import UserFeedbackSurvey

from ._base import DT_STR_FORMAT, BaseTestDataView


def at_example(prefix: str) -> str:
    return f"{prefix}@example.com"  # /PS-IGNORE


class TestExporterDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:exporter-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        exporters = result["results"]
        assert len(exporters) == 4
        assert exporters[0] == {
            "id": 1,
            "is_active": True,
            "name": "Test Exporter 1",
            "registered_number": "111",
            "comments": None,
            "main_exporter_id": None,
            "exclusive_correspondence": True,
        }


class TestImporterDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:importer-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        importers = result["results"]
        assert len(importers) == 5
        assert importers[0] == {
            "id": 1,
            "is_active": True,
            "type": "ORGANISATION",
            "name": "Test Importer 1",
            "registered_number": None,
            "eori_number": "GB1111111111ABCDE",  # /PS-IGNORE
            "region_origin": None,
            "user_id": None,
            "comments": None,
            "main_importer_id": None,
        }

        assert importers[1] == {
            "id": 2,
            "is_active": True,
            "type": "ORGANISATION",
            "name": "Test Importer 1 Agent 1",
            "registered_number": None,
            "eori_number": None,
            "region_origin": None,
            "user_id": None,
            "comments": None,
            "main_importer_id": 1,
        }


class TestOfficeDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:office-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        offices = result["results"]
        assert len(offices) == 9
        assert offices[0] == {
            "id": 1,
            "is_active": True,
            "address_1": "I1 address line 1",
            "address_2": "I1 address line 2",
            "address_3": None,
            "address_4": None,
            "address_5": None,
            "postcode": "BT180LZ",  # /PS-IGNORE
            "eori_number": "GB0123456789ABCDE",  # /PS-IGNORE
            "address_entry_type": "EMPTY",
            "importer_id": 1,
            "exporter_id": None,
        }


class TestUserDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:user-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        users = result["results"]
        email = at_example("access_request_user")

        assert len(users) == 23
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
        assert len(result["results"]) == 1
        assert result["results"][0] == {
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
            "application_id": self.app.pk,
            "created_by_id": self.user.pk,
            "created_datetime": self.survey.created_datetime.strftime(DT_STR_FORMAT),
        }
