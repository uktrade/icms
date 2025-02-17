from typing import Any, Self

from pydantic import BaseModel, model_validator

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/details/
class DetailsKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If summmaryHtml is set, this is not required.
    # Text to use within the summary element (the visible part of the details element).
    # If summaryHtml is provided, the summaryText option will be ignored.
    summaryText: str | None = None
    # Required. If summmaryText is set, this is not required.
    # HTML to use within the summary element (the visible part of the details element).
    # If summaryHtml is provided, the summaryText option will be ignored.
    summaryHtml: str | None = None
    # Required. If html is set, this is not required.
    # Text to use within the disclosed part of the details element.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the disclosed part of the details element.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire details component in a call block.
    caller: Any | None = None
    # ID to add to the details element.
    id: str | None = None
    # If true, details element will be expanded.
    open: bool | None = None
    # Classes to add to the <details> element.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the <details> element.
    attributes: dict[str, Any] | None = None

    @model_validator(mode="after")
    def check_summary_text_or_summary_html_valid(self) -> Self:
        if self.summaryText and self.summaryHtml:
            raise ValueError("Only summaryText or summaryHtml can be entered")

        if not self.summaryText and not self.summaryHtml:
            raise ValueError("summaryText or summaryHtml must be entered")

        return self
