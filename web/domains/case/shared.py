from django.db import models


# Import & Export application statuses
# TODO: ICMSLST-634 see if we can remove the type:ignores once we have django-stubs
class ImpExpStatus(models.TextChoices):
    COMPLETED: str = ("COMPLETED", "Completed")  # type:ignore[assignment]
    DELETED: str = ("DELETED", "Deleted")  # type:ignore[assignment]
    IN_PROGRESS: str = ("IN_PROGRESS", "In Progress")  # type:ignore[assignment]
    PROCESSING: str = ("PROCESSING", "Processing")  # type:ignore[assignment]

    REVOKED: str = ("REVOKED", "Revoked")  # type:ignore[assignment]
    STOPPED: str = ("STOPPED", "Stopped")  # type:ignore[assignment]
    SUBMITTED: str = ("SUBMITTED", "Submitted")  # type:ignore[assignment]
    VARIATION_REQUESTED: str = (
        "VARIATION_REQUESTED",
        "Variation Requested",
    )  # type:ignore[assignment]
    WITHDRAWN: str = ("WITHDRAWN", "Withdrawn")  # type:ignore[assignment]
