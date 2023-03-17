from types import DynamicClassAttribute

from django.db import models


class PermissionTextChoice(models.TextChoices):
    @DynamicClassAttribute
    def codename(self) -> str:
        """A lot of the guardian functions expect a codename value"""

        return self._value_.removeprefix("web.")

    @classmethod
    def get_permissions(cls) -> list[tuple[str, str]]:
        """Return all the class permissions with the "web." prefix removed.

        This is required when setting permissions in a model class.
        e.g.
        class Meta:
            permissions = Perms.obj.exporter.get_permissions()
        """

        return [cls._remove_prefix(v) for v in cls.choices]

    @staticmethod
    def _remove_prefix(v: tuple[str, str]) -> tuple[str, str]:
        value, label = v

        return value.removeprefix("web."), label
