from web.domains.template.constants import TemplateCodes
from web.types import TypedTextChoices

CELERY_MAIL_QUEUE_NAME = "mail"

SEND_EMAIL_TASK_NAME = "web.mail.send_email"
SEND_MAILSHOT_TASK_NAME = "web.mail.send_mailshot_email"
SEND_RETRACT_MAILSHOT_TASK_NAME = "web.mail.send_retract_mailshot_email"
SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME = "web.mail.send_authority_expiring_section_5_email"
SEND_AUTHORITY_EXPIRING_FIREARMS_TASK_NAME = "web.mail.send_authority_expiring_firearms_email"

DATE_FORMAT = "%-d %B %Y"

DEFAULT_APPLICANT_GREETING = "applicant"
DEFAULT_STAFF_GREETING = "colleague"


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
    APPLICATION_UPDATE_WITHDRAWN = ("APPLICATION_UPDATE_WITHDRAWN", "Application Update Withdrawn")

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
    CONSTABULARY_DEACTIVATED_FIREARMS = (
        "CONSTABULARY_DEACTIVATED_FIREARMS",
        "Constabulary Deactivated Firearms",
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
    CASE_EMAIL_WITH_DOCUMENTS = ("CASE_EMAIL_WITH_DOCUMENTS", "Case Email With Documents")
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
    AUTHORITY_ARCHIVED = ("AUTHORITY_ARCHIVED", "Authority Archived")
    AUTHORITY_EXPIRING_SECTION_5 = ("AUTHORITY_EXPIRING_SECTION_5", "Authority Expiring Section 5")
    AUTHORITY_EXPIRING_FIREARMS = ("AUTHORITY_EXPIRING_FIREARMS", "Authority Expiring Firearms")
    MAILSHOT = ("MAILSHOT", "Mailshot")
    RETRACT_MAILSHOT = ("RETRACT_MAILSHOT", "Retract Mailshot")
    NEW_USER_WELCOME = ("NEW_USER_WELCOME", "New User Welcome")
    ORG_CONTACT_INVITE = ("ORG_CONTACT_INVITE", "New Organisation Contact Invite")
    EMAIL_VERIFICATION = ("EMAIL_VERIFICATION", "Email Verification")


class CaseEmailCodes(TypedTextChoices):
    """Class containing all TemplateCodes values that have been used to create CaseEmail Records."""

    BEIS_CASE_EMAIL = (TemplateCodes.CA_BEIS_EMAIL, "Business, Energy & Industrial Strategy Email")
    CONSTABULARY_CASE_EMAIL = (TemplateCodes.IMA_CONSTAB_EMAIL, "Constabulary Email")
    HSE_CASE_EMAIL = (TemplateCodes.CA_HSE_EMAIL, "Health and Safety Email")
    NMIL_CASE_EMAIL = (TemplateCodes.IMA_NMIL_EMAIL, "Nuclear Materials Email")
    SANCTIONS_CASE_EMAIL = (TemplateCodes.IMA_SANCTIONS_EMAIL, "Sanctions Email")
    DEACTIVATE_USER_EMAIL = (TemplateCodes.DEACTIVATE_USER, "Deactivate User Email")
    REACTIVATE_USER_EMAIL = (TemplateCodes.REACTIVATE_USER, "Reactivate User Email")
