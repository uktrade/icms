from pydantic import BaseModel


class ListRowAction(BaseModel):
    label: str
    url: str


class ListRow(BaseModel):
    name: str
    actions: list[ListRowAction] | None = None


class ListWithActionsKwargs(BaseModel):
    """Custom uktrade component for rendering a list of with actions."""

    rows: list[ListRow]
