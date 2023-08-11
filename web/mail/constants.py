from web.types import TypedTextChoices

SEND_EMAIL_TASK_NAME = "web.mail.api.send_email"


class EmailTypes(TypedTextChoices):
    ACCESS_REQUEST = ("ACCESS_REQUEST", "Access Request")
    ACCESS_REQUEST_CLOSED = ("ACCESS_REQUEST_CLOSED", "Access Request Closed")
    CASE_COMPLETE = ("CASE_COMPLETE", "Case Complete")
