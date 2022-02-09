from typing import Any, Generator

from django.db import models


class MigrationBase(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        for field in cls.get_includes():
            new = field.replace("__", "_")
            data[new] = data.pop(field)

        status = data.pop("status", None)

        if status:
            data["is_active"] = status.lower() == "active"

        return data

    @staticmethod
    def get_excludes() -> list[str]:
        return []

    @staticmethod
    def get_includes() -> list[str]:
        return []

    @classmethod
    def get_values(cls) -> list[str]:
        excludes = cls.get_excludes()
        values = cls.get_includes()

        for f in cls._meta.fields:
            name = f"{f.name}_id" if f.is_relation else f.name
            if name not in excludes:
                values.append(name)

        return values

    @classmethod
    def get_related(cls) -> list[str]:
        includes = cls.get_includes()
        return [i.split("__")[0] for i in includes]

    @classmethod
    def get_source_data(cls) -> Generator:
        values = cls.get_values()
        related = cls.get_related()
        return cls.objects.select_related(*related).values(*values).iterator()
