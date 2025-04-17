import datetime as dt
from decimal import Decimal
from types import UnionType

from pydantic import BaseModel

# Config to map the type annotations with the data type in data workspace
# annotation: (data_type, nullable)
ANNOTATION_CONF: dict[type | UnionType, tuple[str, bool]] = {
    bool: ("Boolean", False),
    bool | None: ("Boolean", True),
    Decimal: ("Decimal", False),
    Decimal | None: ("Decimal", True),
    dt.datetime: ("Datetime", False),
    dt.datetime | None: ("Datetime", True),
    int: ("Integer", False),
    int | None: ("Integer", True),
    list[int]: ("ArrayInteger", False),
    list[str]: ("ArrayString", False),
    str: ("String", False),
    str | None: ("String", True),
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
