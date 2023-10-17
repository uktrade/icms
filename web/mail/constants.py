import enum

from web.types import TypedTextChoices

SEND_EMAIL_TASK_NAME = "web.mail.api.send_email"


class EmailTypes(TypedTextChoices):
    ACCESS_REQUEST = ("ACCESS_REQUEST", "Access Request")
    ACCESS_REQUEST_CLOSED = ("ACCESS_REQUEST_CLOSED", "Access Request Closed")
    ACCESS_REQUEST_APPROVAL_COMPLETE = (
        "ACCESS_REQUEST_APPROVAL_COMPLETE",
        "Access Request Approval Complete",
    )
    APPLICATION_COMPLETE = ("APPLICATION_COMPLETE", "Application Complete")
    APPLICATION_VARIATION_REQUEST_COMPLETE = (
        "APPLICATION_VARIATION_REQUEST_COMPLETE",
        "Application Variation Request Complete",
    )
    APPLICATION_EXTENSION_COMPLETE = (
        "APPLICATION_EXTENSION_COMPLETE",
        "Application Extension Complete",
    )
    APPLICATION_STOPPED = ("APPLICATION_STOPPED", "Application Stopped")
    APPLICATION_REFUSED = ("APPLICATION_REFUSED", "Application Refused")
    APPLICATION_REASSIGNED = ("APPLICATION_REASSIGNED", "Application Reassigned")
    APPLICATION_REOPENED = ("APPLICATION_REOPENED", "Application Reopened")
    APPLICATION_UPDATE = ("APPLICATION_UPDATE", "Application Update")
    APPLICATION_UPDATE_RESPONSE = ("APPLICATION_UPDATE_RESPONSE", "Application Update Response")

    EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED = (
        "EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED",
        "Exporter Access Request Approval Opened",
    )
    IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED = (
        "IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED",
        "Importer Access Request Approval Opened",
    )
    FIREARMS_SUPPLEMENTARY_REPORT = (
        "FIREARMS_SUPPLEMENTARY_REPORT",
        "Firearms Supplementary Report",
    )
    WITHDRAWAL_ACCEPTED = ("WITHDRAWAL_ACCEPTED", "Withdrawal Accepted")
    WITHDRAWAL_CANCELLED = ("WITHDRAWAL_CANCELLED", "Withdrawal Cancelled")
    WITHDRAWAL_OPENED = ("WITHDRAWAL_OPENED", "Withdrawal Opened")
    WITHDRAWAL_REJECTED = ("WITHDRAWAL_REJECTED", "Withdrawal Rejected")
    APPLICATION_VARIATION_REQUEST_CANCELLED = (
        "APPLICATION_VARIATION_REQUEST_CANCELLED",
        "Application Variation Request Cancelled",
    )
    APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED = (
        "APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED",
        "Application Variation Request Update Required",
    )
    APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED = (
        "APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED",
        "Application Variation Request Update Cancelled",
    )
    APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED = (
        "APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED",
        "Application Variation Request Update Received",
    )
    APPLICATION_VARIATION_REQUEST_REFUSED = (
        "APPLICATION_VARIATION_REQUEST_REFUSED",
        "Application Variation Request Refused",
    )
    CASE_EMAIL = ("CASE_EMAIL", "Case Email")
    APPLICATION_FURTHER_INFORMATION_REQUEST = (
        "APPLICATION_FURTHER_INFORMATION_REQUEST",
        "Application Further Information Request",
    )
    APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED = (
        "APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED",
        "Application Further Information Request Responded",
    )
    APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN = (
        "APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN",
        "Application Further Information Request Withdrawn",
    )
    ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST = (
        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST",
        "Application Further Information Request",
    )
    ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED = (
        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED",
        "Access Request Further Information Request Responded",
    )
    ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN = (
        "ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN",
        "Access Request Further Information Request Withdrawn",
    )
    LICENCE_REVOKED = ("LICENCE_REVOKED", "Licence Revoked")
    CERTIFICATE_REVOKED = ("CERTIFICATE_REVOKED", "Certificate Revoked")


# TODO: ICMSLST-2348 Gov Notify - Review constants
class VariationRequestDescription(enum.StrEnum):
    CANCELLED = "CANCELLED"
    UPDATE_REQUIRED = "UPDATE_REQUIRED"
    UPDATE_CANCELLED = "UPDATE_CANCELLED"
    UPDATE_RECEIVED = "UPDATE_RECEIVED"
    REFUSED = "REFUSED"


class CaseEmailTemplate(TypedTextChoices):
    IMA_CONSTAB_EMAIL = ("IMA_CONSTAB_EMAIL", "Constabulary Email")
    IMA_SANCTION_EMAIL = ("IMA_SANCTION_EMAIL", "Sanctions Email")
    CA_HSE_EMAIL = ("CA_HSE_EMAIL", "Health and Safety Email")
    CA_BEIS_EMAIL = ("CA_BEIS_EMAIL", "Business, Energy & Industrial Strategy Email")


IMPORT_CASE_EMAILS = [CaseEmailTemplate.IMA_CONSTAB_EMAIL, CaseEmailTemplate.IMA_SANCTION_EMAIL]
EXPORT_CASE_EMAILS = [CaseEmailTemplate.CA_HSE_EMAIL, CaseEmailTemplate.CA_BEIS_EMAIL]
