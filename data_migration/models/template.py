from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.reference.country import Country, CountryTranslationSet
from data_migration.utils.format import (
    reformat_placeholders,
    replace_apos,
    strip_foxid_attribute,
)

from .base import MigrationBase


class Template(MigrationBase):
    is_active = models.BooleanField(default=True)
    template_name = models.CharField(max_length=100)
    template_code = models.CharField(max_length=50, null=True, unique=True)
    template_type = models.CharField(max_length=50, null=False)
    application_domain = models.CharField(max_length=20, null=False)
    country_translation_set = models.ForeignKey(
        CountryTranslationSet, on_delete=models.SET_NULL, null=True
    )


class TemplateVersion(MigrationBase):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True)
    is_active = models.BooleanField()
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=4000, null=True)
    content = models.TextField(null=True)
    created_by = models.ForeignKey("data_migration.User", on_delete=models.PROTECT)
    template_type = models.CharField(max_length=50, null=False)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        content = data["content"]
        template_type = data.pop("template_type")

        # Previous system users are not being migrated to V2, so replace their IDs with 0
        if data["created_by_id"] in [2488, 1576, 804, 21]:
            data["created_by_id"] = 0

        if not content:
            return data

        content = strip_foxid_attribute(content)
        content = replace_apos(content)

        if template_type == "LETTER_TEMPLATE":
            content = reformat_placeholders(content)

        data["content"] = content

        return data


class TemplateCountry(MigrationBase):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class CFSScheduleParagraph(MigrationBase):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="paragraphs")
    ordinal = models.IntegerField()
    name = models.CharField(max_length=100)
    content = models.TextField(null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        content = data["content"]
        data["content"] = content and replace_apos(content)

        return data

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"order": F("ordinal")}

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ordinal"]


class EndorsementTemplate(MigrationBase):
    importapplicationtype = models.ForeignKey(
        "data_migration.ImportApplicationType", on_delete=models.CASCADE
    )
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
