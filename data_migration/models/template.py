from django.db import models

from data_migration.models.reference.country import Country, CountryTranslationSet

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


class TemplateCountry(MigrationBase):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class CFSScheduleParagraph(MigrationBase):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="paragraphs")
    ordinal = models.IntegerField()
    name = models.CharField(max_length=100)
    content = models.TextField(null=True)


class EndorsementTemplate(MigrationBase):
    importapplicationtype = models.ForeignKey(
        "data_migration.ImportApplicationType", on_delete=models.CASCADE
    )
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
