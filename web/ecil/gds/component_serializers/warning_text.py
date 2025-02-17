from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/warning-text/
class WarningTextKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the warning text component.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the warning text component.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # The fallback text for the icon. Defaults to "Warning".
    iconFallbackText: str | None = None
    # Classes to add to the warning text.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the warning text.
    attributes: dict[str, Any] | None = None
