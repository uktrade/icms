from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin
from .tag import TagKwargs


# All options available here:
# https://design-system.service.gov.uk/components/phase-banner/
class PhaseBannerKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the phase banner.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the phase banner.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Required. The tag used by the phase banner component.
    tag: TagKwargs
    # Classes to add to the phase banner container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the phase banner container.
    attributes: dict[str, Any] | None = None
