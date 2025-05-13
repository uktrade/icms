from markupsafe import Markup
from pydantic import BaseModel, ConfigDict


class ListRowAction(BaseModel):
    label: str
    url: str


class ListRow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | Markup
    actions: list[ListRowAction] | None = None


class ListWithActionsKwargs(BaseModel):
    """Custom uktrade component for rendering a list of with actions."""

    rows: list[ListRow]
