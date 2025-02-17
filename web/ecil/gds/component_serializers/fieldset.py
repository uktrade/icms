from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class FieldsetLegend(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the legend.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the legend.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the legend.
    classes: str | None = None
    # Whether the legend also acts as the heading for the page.
    isPageHeading: bool | None = None


# All options available here:
# https://design-system.service.gov.uk/components/fieldset/
class FieldsetKwargs(BaseModel):
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional descriptive information for screenreader users.
    describedBy: str | None = None
    # The legend for the fieldset component.
    legend: FieldsetLegend
    # Classes to add to the fieldset container.
    classes: str | None = None
    # Optional ARIA role attribute.
    role: str | None = None
    # HTML attributes (for example data attributes) to add to the fieldset container.
    attributes: dict[str, Any] | None = None
    # HTML to use/render within the fieldset element.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire fieldset component in a call block.
    caller: Any | None = None
