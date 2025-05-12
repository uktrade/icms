import datetime as dt

import pytest

from web.data_workspace import serializers


class TestUserSerializer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.serializer = serializers.UserSerializer

    def test_serialize_data(self):
        serialized = self.serializer(
            id=1,
            title="Mr",
            first_name="Test",
            last_name="User",
            email="test@exmple.com",  # /PS-IGNORE
            primary_email_address="test@exmple.com",  # /PS-IGNORE
            organisation="Test Org",
            department="Test Dept",
            job_title="Test Job",
            date_joined=dt.date(2024, 2, 1),
            last_login=dt.datetime(2024, 2, 2, 12, 30),
            exporter_ids=[1],
            importer_ids=[],
            group_names=["Exporter User"],
        )

        assert serialized.model_dump(mode="json") == {
            "id": 1,
            "title": "Mr",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@exmple.com",  # /PS-IGNORE
            "primary_email_address": "test@exmple.com",  # /PS-IGNORE
            "organisation": "Test Org",
            "department": "Test Dept",
            "job_title": "Test Job",
            "date_joined": "2024-02-01T00:00:00",
            "last_login": "2024-02-02T12:30:00",
            "exporter_ids": [1],
            "importer_ids": [],
            "group_names": ["Exporter User"],
        }

    def test_table_name(self):
        assert self.serializer.table_name() == "user"

    def test_pk_name(self):
        assert self.serializer.pk_name() == "id"

    def test_table_indexes(self):
        assert self.serializer.table_indexes() == []

    def test_url(self):
        assert self.serializer.url() == "/data-workspace/v0/users/"

    def test_metadata(self):
        metadata = self.serializer.get_metadata()
        assert metadata.model_dump(mode="json", exclude_defaults=True) == {
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
            "table_name": "user",
        }


class TestUserFeedbackSerializer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.serializer = serializers.UserFeedbackSurveySerializer

    def test_table_name(self):
        assert self.serializer.table_name() == "userfeedbacksurvey"

    def test_pk_name(self):
        assert self.serializer.pk_name() == "id"

    def test_table_indexes(self):
        assert self.serializer.table_indexes() == []

    def test_url(self):
        assert self.serializer.url() == "/data-workspace/v0/user-surveys/"

    def test_metadata(self):
        metadata = self.serializer.get_metadata()
        assert metadata.model_dump(mode="json", exclude_defaults=True) == {
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
                    "name": "application_id",
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
            "table_name": "userfeedbacksurvey",
        }
