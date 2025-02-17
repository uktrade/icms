from typing import Any

from pydantic import BaseModel


class Item(BaseModel):
    # The pagination item text – usually a page number.
    number: str | None = None
    # The visually hidden label (for the pagination item) which will be applied to an aria-label and
    # announced by screen readers on the pagination item link. Should include page number.
    visuallyHiddenText: str | None = None
    # Required. The link’s URL.
    href: str
    # Set to true to indicate the current page the user is on.
    current: bool | None = None
    # Use this option if you want to specify an ellipsis at a given point between numbers.
    # If you set this option as true, any other options for the item are ignored.
    ellipsis: bool | None = None
    # The HTML attributes (for example, data attributes) you want to add to the anchor.
    attributes: dict[str, Any] | None = None


class Previous(BaseModel):
    # The text content of the link to the previous page.
    # Defaults to "Previous page", with ‘page’ being visually hidden.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # The HTML content of the link to the previous page.
    # Defaults to "Previous page", with ‘page’ being visually hidden.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # The optional label that goes underneath the link to the previous page, providing further
    # context for the user about where the link goes.
    labelText: str | None = None
    # Required. The previous page’s URL.
    href: str
    # The HTML attributes (for example, data attributes) you want to add to the anchor.
    attributes: dict[str, Any] | None = None


class Next(BaseModel):
    # The text content of the link to the next page.
    # Defaults to "Next page", with ‘page’ being visually hidden.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # The HTML content of the link to the next page.
    # Defaults to "Next page", with ‘page’ being visually hidden.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # The optional label that goes underneath the link to the next page, providing further context
    # for the user about where the link goes.
    labelText: str | None = None
    # Required. The next page’s URL.
    href: str
    # The HTML attributes (for example, data attributes) you want to add to the anchor.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/pagination/
class PaginationKwargs(BaseModel):
    # The items within the pagination component.
    items: list[Item]
    # A link to the previous page, if there is a previous page. See macro options for previous.
    previous: Previous | None = None
    # A link to the next page, if there is a next page.
    next: Next
    # The label for the navigation landmark that wraps the pagination. Defaults to "Pagination".
    landmarkLabel: str | None = None
    # The classes you want to add to the pagination nav parent.
    classes: str | None = None
    # The HTML attributes (for example, data attributes) you want to add to the pagination nav parent.
    attributes: dict[str, Any] | None = None
