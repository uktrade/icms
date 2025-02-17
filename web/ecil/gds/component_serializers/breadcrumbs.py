from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Item(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the breadcrumbs item.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the breadcrumbs item.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Link for the breadcrumbs item. If not specified, breadcrumbs item is a normal list item.
    href: str | None = None
    # HTML attributes (for example data attributes) to add to the individual crumb.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/breadcrumbs/
class BreadcrumbsKwargs(BaseModel):
    # Required. The items within breadcrumbs.
    items: list[Item]
    # Classes to add to the breadcrumbs container.
    classes: str | None = None
    # When true, the breadcrumbs will collapse to the first and last item only on tablet breakpoint and below.
    collapseOnMobile: bool | None = None
    # HTML attributes (for example data attributes) to add to the breadcrumbs container.
    attributes: dict[str, Any] | None = None
    # Plain text label identifying the landmark to screen readers. Defaults to “Breadcrumb”.
    labelText: str | None = None
