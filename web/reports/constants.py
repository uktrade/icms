from web.types import TypedTextChoices


class ReportStatus(TypedTextChoices):
    COMPLETED = ("COMPLETED", "Completed")
    DELETED = ("DELETED", "Deleted")
    IN_PROGRESS = ("IN_PROGRESS", "In Progress")
    PROCESSING = ("PROCESSING", "Processing")
    SUBMITTED = ("SUBMITTED", "Submitted")


class ReportType(TypedTextChoices):
    ISSUED_CERTIFICATES = ("ISSUED_CERTIFICATES", "Issued Certificates")
    ACCESS_REQUESTS = ("ACCESS_REQUESTS", "Access Requests")
    IMPORT_LICENCES = ("IMPORT_LICENCES", "Import Licences")


class DateFilterType(TypedTextChoices):
    SUBMITTED = ("SUBMITTED", "Application Submitted date")
    CLOSED = ("CLOSED", "Application Initially closed date")
