from web.types import TypedTextChoices


# Import & Export application statuses
class ImpExpStatus(TypedTextChoices):
    COMPLETED = ("COMPLETED", "Completed")
    DELETED = ("DELETED", "Deleted")
    IN_PROGRESS = ("IN_PROGRESS", "In Progress")
    PROCESSING = ("PROCESSING", "Processing")

    REVOKED = ("REVOKED", "Revoked")
    STOPPED = ("STOPPED", "Stopped")
    SUBMITTED = ("SUBMITTED", "Submitted")
    VARIATION_REQUESTED = ("VARIATION_REQUESTED", "Variation Requested")
    WITHDRAWN = ("WITHDRAWN", "Withdrawn")
