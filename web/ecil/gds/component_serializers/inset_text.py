from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/inset-text/
class InsetTextKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the inset text component.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the inset text component.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire inset text component in a call block.
    caller: Any | None = None
    # ID attribute to add to the inset text container.
    id: str | None = None
    # Classes to add to the inset text container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the inset text container.
    attributes: dict[str, Any] | None = None
