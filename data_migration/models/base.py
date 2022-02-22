from typing import Any, Generator

from django.db import models


class MigrationBase(models.Model):
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

        status = data.pop("status", None)

        if status:
            data["is_active"] = status.lower() == "active"

        return data

    @classmethod
    def fields(cls) -> list[str]:
        """Returns the field names on the model"""

        return [f"{f.name}_id" if f.is_relation else f.name for f in cls._meta.fields]

    @classmethod
    def get_excludes(cls) -> list[str]:
        """List of fields to be excluded in the V2 import"""

        return []

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
    def get_related(cls) -> list[str]:
        """Generates the the related models to include from get_includes"""

        includes = cls.get_includes()
        return list(set(i.split("__")[0] for i in includes))

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values()
        related = cls.get_related()
        return cls.objects.select_related(*related).values(*values).iterator()


class FileBase(MigrationBase):
    class Meta:
        abstract = True


class Process(MigrationBase):
    process_type = models.CharField(max_length=50, default=None)
    is_active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)
    ima_id = models.IntegerField(null=True, unique=True)

    @classmethod
    def get_excludes(cls):
        return ["ima_id"]
