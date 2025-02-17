from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/tag/
class TagKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the tag component.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the tag component.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the tag.
    attributes: dict[str, Any] | None = None
