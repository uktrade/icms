from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class MetaItem(BaseModel):
    # Required. List item text in the meta section of the footer.
    text: str
    # Required. List item link href attribute in the meta section of the footer.
    href: str
    # HTML attributes (for example data attributes) to add to the anchor in the footer meta section.
    attributes: dict[str, Any] | None = None


class Meta(TextOrHTMLMixin, BaseModel):
    # Title for a meta item section. Defaults to "Support links".
    visuallyHiddenTitle: str | None = None
    # HTML to add to the meta section of the footer, which will appear below any links specified using meta items.
    html: str | None = None
    # Text to add to the meta section of the footer, which will appear below any links specified using meta items.
    # If meta html is specified, this option is ignored.
    text: str | None = None
    # The meta items add content within a unordered list to the meta section of the footer component.
    # These appear above any text or custom html in the meta section.
    items: list[MetaItem] | None = None


class NavigationItem(BaseModel):
    # Required. List item text in the navigation section of the footer.
    text: str
    # Required. List item link href attribute in the navigation section of the footer.
    # Both text and href attributes need to be present to create a link.
    href: str
    # HTML attributes (for example data attributes) to add to the anchor in the footer navigation section.
    attributes: dict[str, Any] | None = None


class Navigation(BaseModel):
    # Required. Title for a section.
    title: str
    # Amount of columns to display items in navigation section of the footer.
    columns: int | None = None
    # Width of each navigation section in the footer.
    # You can pass any Design System grid width here - for example, "one-third", "two-thirds" or "one-half".
    # Defaults to "full".
    width: str
    # The items within the navigation section of the footer component.
    items: list[NavigationItem] | None = None


class ContentLicence(TextOrHTMLMixin, BaseModel):
    # Options for contentLicence object Name 	Type 	Description
    # If html is set, this is not required.
    # If html is provided, the text option will be ignored.
    # If neither are provided, the text for the Open Government Licence is used.
    text: str | None = None
    # If text is set, this is not required.
    # If html is provided, the text option will be ignored.
    # If neither are provided, the text for the Open Government Licence is used.
    # The content licence is inside a <span> element, so you can only add phrasing content to it.
    html: str | None = None


class Copyright(TextOrHTMLMixin, BaseModel):
    # If html is set, this is not required.
    # If html is provided, the text option will be ignored.
    # If neither are provided, "© Crown copyright" is used.
    text: str | None = None
    # If text is set, this is not required.
    # If html is provided, the text option will be ignored.
    # If neither are provided, "© Crown copyright" is used.
    # The copyright notice is inside an <a> element, so you can only use text formatting elements within it.
    html: str | None = None


# All options available here:
# https://design-system.service.gov.uk/components/footer/
class GovUKFooterKwargs(BaseModel):
    # The meta section of the footer after any navigation, before the copyright and license information.
    meta: Meta | None = None
    # The navigation section of the footer before a section break and the copyright and license information.
    navigation: list[Navigation] | None = None
    # The content licence information within the footer component.
    # Defaults to Open Government Licence (OGL) v3 licence.
    contentLicence: ContentLicence | None = None
    # The copyright information in the footer component, this defaults to "© Crown copyright".
    copyright: Copyright | None = None
    # Classes that can be added to the inner container, useful if you want to make the footer full width.
    containerClasses: str | None = None
    # Classes to add to the footer component container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the footer component container.
    attributes: dict[str, Any] | None = None
