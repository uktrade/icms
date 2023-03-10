from typing import Any

from django.db import models
from django.db.models import F

from data_migration import queries
from data_migration.models.reference.country import Country, CountryTranslationSet
from data_migration.utils.format import reformat_placeholders, strip_foxid_attribute

from .base import MigrationBase


class Template(MigrationBase):
    UPDATE_TIMESTAMP_QUERY = queries.template_timestamp_update

    start_datetime = models.DateTimeField(null=False)
    end_datetime = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    template_name = models.CharField(max_length=100)
    template_code = models.CharField(max_length=50, null=True, unique=True)
    template_type = models.CharField(max_length=50, null=False)
    application_domain = models.CharField(max_length=20, null=False)
    template_title = models.CharField(max_length=4000, null=True)
    template_content = models.TextField(null=True)
    country_translation_set = models.ForeignKey(
        CountryTranslationSet, on_delete=models.SET_NULL, null=True
    )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        content = data["template_content"]
        content = content and strip_foxid_attribute(content)

        if data["template_type"] == "LETTER_TEMPLATE":
            content = reformat_placeholders(content)

        data["template_content"] = content

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
