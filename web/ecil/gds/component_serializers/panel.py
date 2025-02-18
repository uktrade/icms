from typing import Any, Self

from pydantic import BaseModel, model_validator

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/panel/
class PanelKwargs(TextOrHTMLMixin, BaseModel):
    # Required. If titleHtml is set, this is not required.
    # Text to use within the panel.
    # If titleHtml is provided, the titleText option will be ignored.
    titleText: str | None = None
    # Required. If titleText is set, this is not required.
    # HTML to use within the panel.
    # If titleHtml is provided, the titleText option will be ignored.
    titleHtml: str | None = None
    # Heading level, from 1 to 6. Default is 1.
    headingLevel: int | None = None
    # Required. If html is set, this is not required.
    # Text to use within the panel content.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the panel content.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire panel component in a call block.
    caller: Any | None = None
    # Classes to add to the panel container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the panel container.
    attributes: dict[str, Any] | None = None

    @model_validator(mode="after")
    def check_title_text_or_title_html_valid(self) -> Self:
        if self.titleText and self.titleHtml:
            raise ValueError("Only titleText or titleHtml can be entered")

        if not self.titleText and not self.titleHtml:
            raise ValueError("titleText or titleHtml must be entered")

        return self
