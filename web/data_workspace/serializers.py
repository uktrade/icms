import datetime as dt
from decimal import Decimal
from types import UnionType

from django.urls import reverse
from pydantic import BaseModel

ANNOTATION_CONF: dict[type | UnionType, tuple[str, bool]] = {
    int: ("Integer", False),
    int | None: ("Integer", True),
    str: ("String", False),
    str | None: ("String", True),
    dt.datetime: ("Datetime", False),
    dt.datetime | None: ("Datetime", True),
    Decimal: ("Decimal", False),
    Decimal | None: ("Decimal", True),
    list[int]: ("ArrayInteger", False),
    list[str]: ("ArrayString", False),
}


class FieldMetadataSerializer(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    nullable: bool = False


class MetadataSerializer(BaseModel):
    table_name: str
    endpoint: str
    indexes: list[str]
    fields: list[FieldMetadataSerializer]


class MetadataListSerializer(BaseModel):
    tables: list[MetadataSerializer]


class BaseSerializer(BaseModel):
    @classmethod
    def get_metadata(cls) -> MetadataSerializer:
        return MetadataSerializer(
            table_name=cls.table_name(),
            endpoint=cls.url(),
            indexes=cls.table_indexes(),
            fields=cls.field_metadata(),
        )

    @classmethod
    def field_metadata(cls) -> list[FieldMetadataSerializer]:
        metadata = []
        for field_name in cls.model_fields:
            field = cls.model_fields[field_name]
            data_type, nullable = ANNOTATION_CONF.get(
                field.annotation, (None, None)  # type:ignore[arg-type]
            )

            if not data_type:
                raise ValueError("Unknown data type")

            metadata.append(
                FieldMetadataSerializer(
                    name=field_name,
                    type=data_type,
                    primary_key=field_name == cls.pk_name(),
                    nullable=nullable,
                )
            )

        return metadata

    @staticmethod
    def pk_name() -> str:
        return "id"

    @classmethod
    def table_name(cls) -> str:
        name = cls.__name__.lower()
        if name.endswith("serializer"):
            return f"{name.split('serializer')[0]}"
        return f"{name}"

    @staticmethod
    def table_indexes() -> list:
        return []

    @staticmethod
    def url() -> str:
        raise NotImplementedError("Url must be defined on the serilaizer class")


class BaseResultsSerializer(BaseModel):
    next: str | None = None


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


class Users(BaseResultsSerializer):
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


DATA_SERIALIZERS: list[type[BaseSerializer]] = [
    UserSerializer,
    UserFeedbackSurveySerializer,
]
