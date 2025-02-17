from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/back-link/
class BackLinkKwargs(TextOrHTMLMixin, BaseModel):
    # Text to use within the back link component.
    # If html is provided, the text option will be ignored. Defaults to "Back".
    text: str | None = None
    # HTML to use within the back link component.
    # If html is provided, the text option will be ignored. Defaults to "Back".
    html: str | None = None
    # Required. The value of the link’s href attribute.
    href: str
    # Classes to add to the anchor tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the anchor tag.
    attributes: dict[str, Any] | None = None
