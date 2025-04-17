import datetime as dt

from django.urls import reverse

from .base import BaseResultsSerializer, BaseSerializer


class UserSerializer(BaseSerializer):
    id: int
    title: str | None
    first_name: str
    last_name: str
    email: str
    primary_email_address: str | None
    organisation: str | None
    department: str | None
    job_title: str | None
    date_joined: dt.datetime | None
    last_login: dt.datetime | None
    exporter_ids: list[int]
    importer_ids: list[int]
    group_names: list[str]

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:user-data", kwargs={"version": "v0"})


class UserListSerializer(BaseResultsSerializer):
    results: list[UserSerializer]


class UserFeedbackSurveySerializer(BaseSerializer):
    id: int
    satisfaction: str
    issues: list[str]
    issue_details: str
    find_service: str
    find_service_details: str
    additional_support: str
    service_improvements: str
    future_contact: str
    referrer_path: str
    site: str
    process_id: int | None
    created_by_id: int
    created_datetime: dt.datetime

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:user-survey-data", kwargs={"version": "v0"})


class UserFeedbackSurveys(BaseResultsSerializer):
    results: list[UserFeedbackSurveySerializer]


class ExporterSerializer(BaseSerializer):
    id: int
    is_active: bool
    name: str
    registered_number: str | None
    comments: str | None
    main_exporter_id: int | None
    exclusive_correspondence: bool

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:exporter-data", kwargs={"version": "v0"})


class ExporterListSerializer(BaseResultsSerializer):
    results: list[ExporterSerializer]


class ImporterSerializer(BaseSerializer):
    id: int
    is_active: bool
    type: str
    name: str | None
    registered_number: str | None
    eori_number: str | None
    region_origin: str | None
    user_id: int | None
    comments: str | None
    main_importer_id: int | None

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:importer-data", kwargs={"version": "v0"})


class ImporterListSerializer(BaseResultsSerializer):
    results: list[ImporterSerializer]


class OfficeSerializer(BaseSerializer):
    id: int
    is_active: bool
    address_1: str
    address_2: str | None
    address_3: str | None
    address_4: str | None
    address_5: str | None
    postcode: str | None
    eori_number: str | None
    address_entry_type: str
    importer_id: int | None
    exporter_id: int | None

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:office-data", kwargs={"version": "v0"})


class OfficeListSerializer(BaseResultsSerializer):
    results: list[OfficeSerializer]
