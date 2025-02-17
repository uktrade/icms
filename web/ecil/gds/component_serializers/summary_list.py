from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class RowKey(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within each key.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within each key.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the key wrapper.
    classes: str | None = None


class RowValue(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within each value.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within each value.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the value wrapper.
    classes: str | None = None


class RowActionItem(TextOrHTMLMixin, BaseModel):
    # Required. The value of the link’s href attribute for an action item.
    href: str
    # Required. If html is set, this is not required.
    # Text to use within each action item.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within each action item.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Actions rely on context from the surrounding content so may require additional accessible text.
    # Text supplied to this option is appended to the end. Use html for more complicated scenarios.
    visuallyHiddenText: str | None = None
    # Classes to add to the action item.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the action item.
    attributes: dict[str, Any] | None = None


class RowActions(BaseModel):
    # The action link items within the row item of the summary list component.
    items: list[RowActionItem] | None = None
    # Classes to add to the actions wrapper.
    classes: str | None = None


class Row(BaseModel):
    # Classes to add to the row div.
    classes: str | None = None
    # Required. The reference content (key) for each row item in the summary list component.
    key: RowKey
    # Required. The value for each row item in the summary list component.
    value: RowValue
    # The action link content for each row item in the summary list component.
    actions: RowActions | None = None


class CardTitle(TextOrHTMLMixin, BaseModel):
    # Text to use within each title.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Text to use within each title.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Heading level, from 1 to 6. Default is 2.
    headingLevel: int
    # Classes to add to the title wrapper.
    classes: str | None = None


class CardActionItem(TextOrHTMLMixin, BaseModel):
    # Required. The value of the link’s href attribute for an action item.
    href: str
    # Required. If html is set, this is not required. Text to use within each action item. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within each action item. If html is provided, the text option will be ignored.
    html: str | None = None
    # Actions rely on context from the surrounding content so may require additional accessible text.
    # Text supplied to this option is appended to the end.
    # Use html for more complicated scenarios.
    visuallyHiddenText: str
    # Classes to add to the action item.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the action item.
    attributes: dict[str, Any] | None = None


class CardActions(BaseModel):
    # The action link items shown in the header within the summary card wrapped around the summary list component.
    items: list[CardActionItem] | None = None
    # Classes to add to the actions wrapper.
    classes: str | None = None


class Card(BaseModel):
    # Data for the summary card header.
    title: CardTitle | None = None
    # The action link content shown in the header of each summary card wrapped around the summary list component.
    actions: CardActions | None = None
    # Classes to add to the container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the container.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/summary-list/
class SummaryListKwargs(BaseModel):
    # Required. The rows within the summary list component.
    rows: list[Row]
    # Can be used to wrap a summary card around the summary list component.
    # If any of these options are present, a summary card will wrap around the summary list.
    card: Card | None = None
    # Classes to add to the container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the container.
    attributes: dict[str, Any] | None = None
