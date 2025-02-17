from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Panel(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within each tab panel.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within each tab panel.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # HTML attributes (for example data attributes) to add to the tab panel.
    attributes: dict[str, Any] | None = None


class Item(BaseModel):
    # Required. Specific ID attribute for the tab item. If omitted, then idPrefix string is required instead.
    id: str
    # Required. The text label of a tab item.
    label: str
    # HTML attributes (for example data attributes) to add to the tab.
    attributes: dict[str, Any] | None = None
    # Required. The contents of each tab within the tabs component. This is referenced as a panel.
    panel: Panel


# All options available here:
# https://design-system.service.gov.uk/components/tabs/
class TabsKwargs(BaseModel):
    # This is used for the main component and to compose the ID attribute for each item.
    id: str | None = None
    # Optional prefix.
    # This is used to prefix the id attribute for each tab item and panel, separated by -.
    idPrefix: str | None = None
    # Title for the tabs table of contents.
    title: str | None = None
    # Required. The individual tabs within the tabs component.
    items: list[Item]
    # Classes to add to the tabs component.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the tabs component.
    attributes: dict[str, Any] | None = None
