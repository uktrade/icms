from collections.abc import Generator
from typing import Any

from django.db import models


class MigrationBase(models.Model):
    PROCESS_PK: bool = False

    class Meta:
        abstract = True

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Formats the data dictionary for the model instance ready for export to V2

        :param data: The dictionary of data for the model instance
        """

        for field in cls.get_includes():
            new = field.replace("__", "_")
            data[new] = data.pop(field)

        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Returns the data required to populate the M2M through table for a model

        :param data: The dictionary of data for the model instance
        """

        return cls.data_export(data)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        """Returns a list of the model names that will be populated from data retrieved from V1"""

        return [cls.__name__]

    @classmethod
    def fields(cls) -> list[str]:
        """Returns the field names on the model"""

        return [f"{f.name}_id" if f.is_relation else f.name for f in cls._meta.fields]

    @classmethod
    def get_excludes(cls) -> list[str]:
        """List of fields to be excluded in the V2 import"""

        return [
            field
            for field in cls.fields()
            if field.endswith("_xml") or field in ["legacy_ordinal", "legacy_id"]
        ]

    @classmethod
    def get_includes(cls) -> list[str]:
        """List of fields to fetch through fk relationships for the V2 import"""

        return []

    @classmethod
    def get_values(cls) -> list[str]:
        """List of values to be returned when querying the model for the V2 import"""

        excludes = cls.get_excludes()
        values = cls.get_includes()
        values += [f for f in cls.fields() if f not in excludes]

        return values

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        """Dict of values to be returned when querying the model for the V2 import"""

        return {}

    @classmethod
    def get_related(cls) -> list[str]:
        """Generates the the related models to include from get_includes"""

        includes = cls.get_includes()
        return list({i.split("__")[0] for i in includes})

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()
        related = cls.get_related()
        return (
            cls.objects.select_related(*related)
            .order_by("pk")
            .values(*values, **values_kwargs)
            .iterator(chunk_size=2000)
        )

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        """Queries the model to get the queryset of data for the M2M through table"""

        return cls.get_source_data()
