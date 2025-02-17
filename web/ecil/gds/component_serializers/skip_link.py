from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/skip-link/
class SkipLinkKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the skip link component.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the skip link component.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # The value of the skip link’s href attribute.
    # Defaults to "#content" if you do not provide a value.
    href: str
    # Classes to add to the skip link.
    classes: str
    # HTML attributes (for example data attributes) to add to the skip link.
    attributes: dict[str, Any] | None = None
