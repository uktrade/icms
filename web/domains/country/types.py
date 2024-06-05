from web.types import TypedTextChoices


class CountryGroupName(TypedTextChoices):
    """Country group name constants (taken from V1 live)"""

    #
    # Export Applications
    #
    CFS = "CFS", "Certificate of Free Sale Countries"
    CFS_COM = "CFS_COM", "Certificate of Free Sale Country of Manufacture Countries"
    COM = "COM", "Certificate of Manufacture Countries"
    GMP = "GMP", "Goods Manufacturing Practice Countries"

    #
    # Import Applications
    #
    FA_DFL_IC = "FA_DFL_IC", "Firearms and Ammunition (Deactivated) Issuing Countries"
    FA_OIL_COC = "FA_OIL_COC", "Firearms and Ammunition (OIL) COCs"
    FA_OIL_COO = "FA_OIL_COO", "Firearms and Ammunition (OIL) COOs"
    FA_SIL_COC = "FA_SIL_COC", "Firearms and Ammunition (SIL) COCs"
    FA_SIL_COO = "FA_SIL_COO", "Firearms and Ammunition (SIL) COOs"
    SANCTIONS_COC_COO = "SANCTIONS_COC_COO", "Adhoc application countries"
    SANCTIONS = "SANCTIONS", "Sanctions and adhoc licence countries"
    WOOD_COO = "WOOD_COO", "Wood (Quota) COOs"

    #
    # Utility
    #
    EU = "EU", "All EU countries"
    NON_EU = "NON_EU", "Non EU Single Countries"

    #
    # Inactive Import Applications
    #
    DEROGATION_FROM_SANCTION_COO = "DEROGATION_COO", "Derogation from Sanctions COOs"
    IRON = "IRON_COO", "Iron and Steel (Quota) COOs"
    OPT_COO = "OPT_COO", "OPT COOs"
    OPT_TEMP_EXPORT_COO = "OPT_TEMP_EXPORT_COO", "OPT Temp Export COOs"
    TEXTILES_COO = "TEXTILES_COO", "Textile COOs"
