from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin
from .tag import TagKwargs


class ItemTitle(TextOrHTMLMixin, BaseModel):
    # Required. Text to use within the title.
    # If html is provided, the text argument will be ignored.
    text: str | None = None
    # Required. HTML to use within the title.
    # If html is provided, the text argument will be ignored.
    html: str | None = None
    # Classes to add to the title wrapper.
    classes: str | None = None


class ItemHint(TextOrHTMLMixin, BaseModel):
    # Required. Text to use within the hint.
    # If html is provided, the text argument will be ignored.
    text: str | None = None
    # Required. HTML to use within the hint.
    # If html is provided, the text argument will be ignored.
    html: str | None = None


class ItemStatus(TextOrHTMLMixin, BaseModel):
    # Can be used to add a tag to the status of the task within the task list component.
    tag: TagKwargs | None = None
    # Text to use for the status, as an alternative to using a tag.
    # If html or tag is provided, the text argument will be ignored.
    text: str | None = None
    # HTML to use for the status, as an alternative to using a tag.
    # If html or tag is provided, the text argument will be ignored.
    html: str | None = None
    # Classes to add to the status container.
    classes: str | None = None


class Item(BaseModel):
    # Required. The main title for the task within the task list component.
    title: ItemTitle
    # Can be used to add a hint to each task within the task list component.
    hint: ItemHint | None = None
    # Required. The status for each task within the task list component.
    status: ItemStatus
    # The value of the link’s href attribute for the task list item.
    href: str | None = None
    # Classes to add to the item div.
    classes: str | None = None


# All options available here:
# https://design-system.service.gov.uk/components/task-list/
class TaskListKwargs(BaseModel):
    # Required. The items for each task within the task list component.
    items: list[Item]
    # Classes to add to the ul container for the task list.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the ul container for the task list.
    attributes: dict[str, Any] | None = None
    # Optional prefix.
    # This is used to prefix the id attribute for the task list item tag and hint, separated by -.
    # Defaults to "task-list".
    idPrefix: str | None = None
