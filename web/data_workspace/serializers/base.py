import datetime as dt
import re
from decimal import Decimal
from types import UnionType

from django.urls import reverse
from pydantic import BaseModel

# Config to map the type annotations with the data type in data workspace
# annotation: (data_type, nullable)
ANNOTATION_CONF: dict[type | UnionType, tuple[str, bool]] = {
    bool: ("Boolean", False),
    bool | None: ("Boolean", True),
    Decimal: ("Float", False),
    Decimal | None: ("Float", True),
    dt.date | None: ("Date", True),
    dt.date: ("Date", False),
    dt.datetime | None: ("Datetime", True),
    dt.datetime: ("Datetime", False),
    int: ("Integer", False),
    int | None: ("Integer", True),
    list[int]: ("ArrayInteger", False),
    list[str]: ("ArrayString", False),
    str: ("String", False),
    str | None: ("String", True),
}

ASDECIMAL_ANNOTATIONS = (Decimal, Decimal | None)


class FieldMetadataSerializer(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    nullable: bool = False
    asdecimal: bool = False


class MetadataSerializer(BaseModel):
    table_name: str
    endpoint: str
    indexes: list[str]
    fields: list[FieldMetadataSerializer]


class MetadataListSerializer(BaseModel):
    tables: list[MetadataSerializer]


class BaseSerializer(BaseModel):
    id: int

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
                raise ValueError(f"Unmapped data type: {str(field.annotation)}")

            asdecimal = field.annotation in ASDECIMAL_ANNOTATIONS

            metadata.append(
                FieldMetadataSerializer(
                    name=field_name,
                    type=data_type,
                    primary_key=field_name == cls.pk_name(),
                    nullable=nullable,
                    asdecimal=asdecimal,
                )
            )

        return metadata

    @staticmethod
    def pk_name() -> str:
        return "id"

    @classmethod
    def table_name(cls) -> str:
        split_name = re.findall(r"[A-Z][^A-Z]*", cls.__name__)
        return "-".join(s.lower() for s in split_name if s.lower() != "serializer")

    @staticmethod
    def table_indexes() -> list:
        return []

    @classmethod
    def url(cls) -> str:
        slug_name = cls.table_name()
        return reverse(f"data-workspace:{slug_name}-data", kwargs={"version": "v0"})


class BaseResultsSerializer(BaseModel):
    next: str | None = None


class ApplicationBaseSerializer(BaseSerializer):
    # Process fields
    process_type: str
    is_active: bool
    created: dt.datetime
    finished: dt.datetime | None

    # Application fields
    status: str
    applicant_reference: str | None
    application_type_code: str
    contact_id: int | None
    submit_datetime: dt.datetime
    last_submit_datetime: dt.datetime | None
    reassign_datetime: dt.datetime | None
    reference: str
    decision: str | None
    refuse_reason: str | None
    agent_id: int | None
    agent_office_id: int | None
    last_update_datetime: dt.datetime
    last_updated_by_id: int
    variation_number: int
    created_by_id: int
    submitted_by_id: int
