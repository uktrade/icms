import enum


class TemplateCodes(enum.StrEnum):
    CASE_REOPEN = "CASE_REOPEN"  # Archived
    CA_APPLICATION_UPDATE_EMAIL = "CA_APPLICATION_UPDATE_EMAIL"
    CA_BEIS_EMAIL = "CA_BEIS_EMAIL"
    CA_HSE_EMAIL = "CA_HSE_EMAIL"
    CA_RFI_EMAIL = "CA_RFI_EMAIL"
    CERTIFICATE_REVOKE = "CERTIFICATE_REVOKE"  # Archived
    CFS_SCHEDULE_ENGLISH = "CFS_SCHEDULE_ENGLISH"
    CFS_SCHEDULE_TRANSLATION = "CFS_SCHEDULE_TRANSLATION"
    COVER_FIREARMS_ANTI_PERSONNEL_MINES = "COVER_FIREARMS_ANTI_PERSONNEL_MINES"  # Archived
    COVER_FIREARMS_DEACTIVATED_FIREARMS = "COVER_FIREARMS_DEACTIVATED_FIREARMS"
    COVER_FIREARMS_OIL = "COVER_FIREARMS_OIL"
    COVER_FIREARMS_OUTSIDE_EU = "COVER_FIREARMS_OUTSIDE_EU"  # Archived
    COVER_FIREARMS_PROOF_HOUSE = "COVER_FIREARMS_PROOF_HOUSE"  # Archived
    COVER_FIREARMS_SEC5_EC = "COVER_FIREARMS_SEC5_EC"  # Archived
    COVER_FIREARMS_SEC5_EC_OUTSIDE_DIRECTIVE = (
        "COVER_FIREARMS_SEC5_EC_OUTSIDE_DIRECTIVE"  # Archived
    )
    COVER_FIREARMS_SEC5_NOT_EU = "COVER_FIREARMS_SEC5_NOT_EU"  # Archived
    COVER_FIREARMS_SEC5_N_IRELAND = "COVER_FIREARMS_SEC5_N_IRELAND"  # Archived
    COVER_FIREARMS_SIIL = "COVER_FIREARMS_SIIL"
    DEACTIVATE_USER = "DEACTIVATE_USER"
    FIREARMS_MARKINGS_NON_STANDARD = "FIREARMS_MARKINGS_NON_STANDARD"
    FIREARMS_MARKINGS_STANDARD = "FIREARMS_MARKINGS_STANDARD"
    IAR_RFI_EMAIL = "IAR_RFI_EMAIL"
    IMA_APP_UPDATE = "IMA_APP_UPDATE"
    IMA_CONSTAB_EMAIL = "IMA_CONSTAB_EMAIL"
    IMA_GEN_DECLARATION = "IMA_GEN_DECLARATION"
    IMA_NMIL_EMAIL = "IMA_NMIL_EMAIL"
    IMA_OPT_DECLARATION = "IMA_OPT_DECLARATION"  # Archived
    IMA_RFI = "IMA_RFI"
    IMA_SANCTIONS_RFI = "IMA_SANCTIONS_RFI"
    IMA_SANCTIONS_EMAIL = "IMA_SANCTIONS_EMAIL"
    IMA_SPS_DECLARATION = "IMA_SPS_DECLARATION"
    IMA_WD_DECLARATION = "IMA_WD_DECLARATION"
    LICENCE_REVOKE = "LICENCE_REVOKE"  # Archived
    PUBLISH_MAILSHOT = "PUBLISH_MAILSHOT"
    REACTIVATE_USER = "REACTIVATE_USER"
    RETRACT_MAILSHOT = "RETRACT_MAILSHOT"
    SCHEDULE_FIREARMS_SEC5_EC = "SCHEDULE_FIREARMS_SEC5_EC"  # Archived
    STOP_CASE = "STOP_CASE"  # Archived
