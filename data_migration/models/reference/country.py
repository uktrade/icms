from typing import Any

from django.db import models

from data_migration.models.base import MigrationBase
from web.domains.country.types import CountryGroupName


class Country(MigrationBase):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=4000, null=False)
    type = models.CharField(max_length=30, null=False)
    commission_code = models.CharField(max_length=20, null=False)
    hmrc_code = models.CharField(max_length=20, null=False)


class CountryGroup(MigrationBase):
    country_group_id = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=4000, null=False, unique=True)
    comments = models.CharField(max_length=4000, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        label = data["name"]
        data["name"] = cls.get_v2_name_value(label)

        return data

    @staticmethod
    def get_v2_name_value(label: str) -> CountryGroupName:
        """Match the V1 Country Group Name to V2 Country Group value.

        The labels between V1 and V2 have diverged so map them manually here.
        """

        match label:
            case "Certificate of Free Sale Countries":
                return CountryGroupName.CFS
            case "Certificate of Free Sale Country of Manufacture Countries":
                return CountryGroupName.CFS_COM
            case "Certificate of Manufacture Countries":
                return CountryGroupName.COM
            case "Goods Manufacturing Practice Countries":
                return CountryGroupName.GMP
            case "Firearms and Ammunition (Deactivated) Issuing Countries":
                return CountryGroupName.FA_DFL_IC
            case "Firearms and Ammunition (OIL) COCs":
                return CountryGroupName.FA_OIL_COC
            case "Firearms and Ammunition (OIL) COOs":
                return CountryGroupName.FA_OIL_COO
            case "Firearms and Ammunition (SIL) COCs":
                return CountryGroupName.FA_SIL_COC
            case "Firearms and Ammunition (SIL) COOs":
                return CountryGroupName.FA_SIL_COO
            case "Adhoc application countries":
                return CountryGroupName.SANCTIONS_COC_COO
            case "Sanctions and adhoc licence countries":
                return CountryGroupName.SANCTIONS
            case "Wood (Quota) COOs":
                return CountryGroupName.WOOD_COO
            case "EU":
                return CountryGroupName.EU
            case "Non EU Single Countries":
                return CountryGroupName.NON_EU
            case "Derogation from Sanctions COOs":
                return CountryGroupName.DEROGATION_FROM_SANCTION_COO
            case "Iron and Steel (Quota) COOs":
                return CountryGroupName.IRON
            case "OPT COOs":
                return CountryGroupName.OPT_COO
            case "OPT Temp Export COOs":
                return CountryGroupName.OPT_TEMP_EXPORT_COO
            case "Textile COOs":
                return CountryGroupName.TEXTILES_COO

        raise ValueError(f"Unknown label: {label!r}")

    @classmethod
    def get_excludes(cls):
        return ["country_group_id"]


class CountryGroupCountry(MigrationBase):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    countrygroup = models.ForeignKey(CountryGroup, on_delete=models.CASCADE)


class CountryTranslationSet(MigrationBase):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=100, null=False)


class CountryTranslation(MigrationBase):
    translation = models.CharField(max_length=150, null=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=False)
    translation_set = models.ForeignKey(CountryTranslationSet, on_delete=models.CASCADE)
