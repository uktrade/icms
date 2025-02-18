from typing import Any, Self

from pydantic import BaseModel, model_validator

from .common import TextOrHTMLMixin


class Error(TextOrHTMLMixin, BaseModel):
    # Href attribute for the error link item. If provided item will be an anchor.
    href: str | None = None
    # Required. If html is set, this is not required. Text for the error link item. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML for the error link item. If html is provided, the text option will be ignored.
    html: str | None = None
    # HTML attributes (for example data attributes) to add to the error link anchor.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/error-summary/
class ErrorSummaryKwargs(BaseModel):
    # Required. If titleHtml is set, this is not required.
    # Text to use for the heading of the error summary block.
    # If titleHtml is provided, titleText will be ignored.
    titleText: str | None = None
    # Required. If titleText is set, this is not required.
    # HTML to use for the heading of the error summary block.
    # If titleHtml is provided, titleText will be ignored.
    titleHtml: str | None = None
    # Text to use for the description of the errors.
    # If you set descriptionHtml, the component will ignore descriptionText.
    descriptionText: str | None = None
    # HTML to use for the description of the errors.
    # If you set this option, the component will ignore descriptionText.
    descriptionHtml: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire error summary component in a call block.
    caller: Any | None = None
    # A list of errors to include in the error summary.
    errorList: list[Error]
    # Prevent moving focus to the error summary when the page loads.
    disableAutoFocus: bool | None = None
    # Classes to add to the error-summary container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the error-summary container.
    attributes: dict[str, Any] | None = None

    @model_validator(mode="after")
    def check_title_text_or_title_html_valid(self) -> Self:
        if self.titleText and self.titleHtml:
            raise ValueError("Only titleText or titleHtml can be entered")

        if not self.titleText and not self.titleHtml:
            raise ValueError("titleText or titleHtml must be entered")

        return self
