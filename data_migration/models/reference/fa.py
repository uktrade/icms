from django.db import models

from data_migration.models.base import MigrationBase


class Constabulary(MigrationBase):
    name = models.CharField(max_length=50, null=False)
    region = models.CharField(max_length=3, null=False)
    email = models.EmailField(max_length=254, null=False)
    is_active = models.BooleanField(null=False, default=True)


class ObsoleteCalibreGroup(MigrationBase):
    legacy_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200, null=False)
    is_active = models.BooleanField(null=False, default=True)
    order = models.IntegerField(null=False)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_id"]


class ObsoleteCalibre(MigrationBase):
    legacy_id = models.IntegerField(unique=True)
    calibre_group = models.ForeignKey(
        ObsoleteCalibreGroup,
        on_delete=models.CASCADE,
        to_field="legacy_id",
        null=False,
    )
    name = models.CharField(max_length=200, null=False)
    is_active = models.BooleanField(null=False, default=True)
    order = models.IntegerField(null=False)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["calibre_group_id", "legacy_id"]

    @classmethod
    def get_includes(cls) -> list[str]:
        return super().get_includes() + ["calibre_group__id"]
