import enum


class DatabaseEmailTemplate(enum.StrEnum):
    CASE_REOPEN = "CASE_REOPEN"
    CERTIFICATE_REVOKE = "CERTIFICATE_REVOKE"
    LICENCE_REVOKE = "LICENCE_REVOKE"
    STOP_CASE = "STOP_CASE"


class VariationRequestDescription(enum.StrEnum):
    CANCELLED = "CANCELLED"
    UPDATE_REQUIRED = "UPDATE_REQUIRED"
    UPDATE_CANCELLED = "UPDATE_CANCELLED"
    UPDATE_RECEIVED = "UPDATE_RECEIVED"
    REFUSED = "REFUSED"