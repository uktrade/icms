from web.types import TypedTextChoices


class EmailTypes(TypedTextChoices):
    ACCESS_REQUEST = ("ACCESS_REQUEST", "Access Request")
    CASE_COMPLETE = ("CASE_COMPLETE", "Case Complete")
