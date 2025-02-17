from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/error-message/
class ErrorMessageKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the error message. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the error message. If html is provided, the text option will be ignored.
    html: str | None = None
    # ID attribute to add to the error message <p> tag.
    id: str | None = None
    # Classes to add to the error message <p> tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the error message <p> tag.
    attributes: dict[str, Any] | None = None
    # A visually hidden prefix used before the error message. Defaults to "Error".
    visuallyHiddenText: str | None = None
