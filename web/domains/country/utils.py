from django.db.models import QuerySet

from web.models import Country, CountryGroup
from web.types import TypedTextChoices


# TODO: ICMSLST-2671 Move to CountryGroup model as part of wider country refactor.
class CountryGroupName(TypedTextChoices):
    """Country group name constants (taken from V1 live)"""

    ADHOC_APP_COUNTRIES = "Adhoc application countries"
    CFS = "Certificate of Free Sale Countries"
    CFS_COM = "Certificate of Free Sale Country of Manufacture Countries"
    COM = "Certificate of Manufacture Countries"
    DEROGATION_FROM_SANCTION_COO = "Derogation from Sanctions COOs"
    EU = ("EU", "All EU countries")
    FA_DFL_IC = "Firearms and Ammunition (Deactivated) Issuing Countries"
    FA_OIL_COC = "Firearms and Ammunition (OIL) COCs"
    FA_OIL_COO = "Firearms and Ammunition (OIL) COOs"
    FA_DFL_COC = "Firearms and Ammunition (SIL) COCs"
    FA_DFL_COO = "Firearms and Ammunition (SIL) COOs"
    GMP = "Goods Manufacturing Practice Countries"
    IRON = "Iron and Steel (Quota) COOs"
    NON_EU = "Non EU Single Countries"
    OPT_COC = "OPT COOs"
    OPT_TEMP_EXPORT_COO = "OPT Temp Export COOs"
    SANCTIONS = "Sanctions and adhoc licence countries"
    TEXTILES_COO = "Textile COOs"
    WOOD_COO = "Wood (Quota) COOs"


def get_eu_countries() -> QuerySet[Country]:
    return get_country_group_countries(CountryGroupName.EU)


def get_country_group_countries(name: CountryGroupName) -> QuerySet[Country]:
    return CountryGroup.objects.get(name=name).countries.filter(is_active=True)
