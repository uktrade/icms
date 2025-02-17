from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Heading(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. The heading text of each section.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. The heading HTML content of each section.
    # The header is inside the HTML <button> element, so you can only add phrasing content to it.
    # If html is provided, the text option will be ignored.
    html: str | None = None


class Summary(TextOrHTMLMixin, BaseModel):
    # The summary line text content of each section. If html is provided, the text option will be ignored.
    text: str | None = None
    # The summary line HTML content of each section. The summary line is inside the HTML <button>
    # element, so you can only add phrasing content to it. If html is provided, the text option will be ignored.
    html: str | None = None


class Content(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. The text content of each section, which is
    # hidden when the section is closed. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. The HTML content of each section, which is
    # hidden when the section is closed. If html is provided, the text option will be ignored.
    html: str | None = None


class Item(BaseModel):
    # Required. The heading of each accordion section. See macro options for items heading.
    heading: Heading
    # The summary line of each accordion section. See macro options for items summary.
    summary: Summary
    # Required. The content of each accordion section. See macro options for items content.
    content: Content
    # Sets whether the section should be expanded when the page loads for the first time. Defaults to false.
    expanded: bool | None = None


# All options available here:
# https://design-system.service.gov.uk/components/accordion/
class AccordionKwargs(BaseModel):
    # Required. Must be unique across the domain of your service if rememberExpanded is true
    # (as the expanded state of individual instances of the component persists across page loads
    # using session storage).
    # Used as an id in the HTML for the accordion as a whole, and also as a prefix for the ids of
    # the section contents and the buttons that open them, so that those ids can be the target of
    # aria-control attributes.
    id: str
    # Heading level, from 1 to 6. Default is 2.
    headingLevel: int | None = None
    # Classes to add to the accordion.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the accordion.
    attributes: dict[str, Any] | None = None
    # Whether the expanded/collapsed state of the accordion should be saved when a user leaves the page and restored when they return. Default is true.
    rememberExpanded: bool | None = None
    # The text content of the ‘Hide all sections’ button at the top of the accordion when all sections are expanded.
    hideAllSectionsText: str | None = None
    # The text content of the ‘Hide’ button within each section of the accordion, which is visible when the section is expanded.
    hideSectionText: str | None = None
    # Text made available to assistive technologies, like screen-readers, as the final part of the
    # toggle’s accessible name when the section is expanded. Defaults to "Hide this section".
    hideSectionAriaLabelText: str | None = None
    # The text content of the ‘Show all sections’ button at the top of the accordion when at least one section is collapsed.
    showAllSectionsText: str | None = None
    # The text content of the ‘Show’ button within each section of the accordion, which is visible when the section is collapsed.
    showSectionText: str | None = None
    # Text made available to assistive technologies, like screen-readers, as the final part of the
    # toggle’s accessible name when the section is collapsed. Defaults to "Show this section".
    showSectionAriaLabelText: str | None = None
    # Required. The sections within the accordion.
    items: list[Item]
