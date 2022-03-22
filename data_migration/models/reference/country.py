from django.db import models

from data_migration.models.base import MigrationBase


class Country(MigrationBase):
    name = models.CharField(max_length=4000, null=False)
    status = models.CharField(max_length=10, null=False)
    type = models.CharField(max_length=30, null=False)
    commission_code = models.CharField(max_length=20, null=False)
    hmrc_code = models.CharField(max_length=20, null=False)


class CountryGroup(MigrationBase):
    country_group_id = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=4000, null=False, unique=True)
    comments = models.CharField(max_length=4000, null=True)

    @staticmethod
    def get_excludes():
        return ["country_group_id"]


class CountryGroupCountry(MigrationBase):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    countrygroup = models.ForeignKey(CountryGroup, on_delete=models.CASCADE)


class CountryTranslationSet(MigrationBase):
    name = models.CharField(max_length=100, null=False)
    status = models.CharField(max_length=10, null=False)


class CountryTranslation(MigrationBase):
    translation = models.CharField(max_length=150, null=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=False)
    translation_set = models.ForeignKey(CountryTranslationSet, on_delete=models.CASCADE)
