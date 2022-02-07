from typing import Any

from django.db import models


class MigrationBase(models.Model):
    class Meta:
        abstract = True

    def excludes(self) -> list[str]:
        return ["_state"]

    def data_export(self) -> dict[str:Any]:
        excludes = self.excludes()
        return {k: v for k, v in self.__dict__.items() if k not in excludes}
