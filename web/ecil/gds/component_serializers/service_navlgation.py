from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Navigation(TextOrHTMLMixin, BaseModel):
    # If true, indicates that the user is currently on this page. This takes precedence over active.
    current: bool | None = None
    # If true, indicates that the user is within this group of pages in the navigation hierarchy.
    active: bool | None = None
    # html 	string 	Required. HTML for the navigation item. If html is provided, the text option will be ignored.
    html: str | None = None
    # text 	string 	Required. Text for the navigation item. If html is provided, the text option will be ignored.
    text: str | None = None
    # URL of the navigation item anchor.
    href: str | None = None
    # HTML attributes (for example data attributes) to add to the navigation item anchor.
    attributes: dict[str, Any] | None = None


class Slots(BaseModel):
    # HTML injected at the start of the service header container.
    start: str | None = None
    # HTML injected at the end of the service header container.
    end: str | None = None
    # HTML injected before the first list item in the navigation list. Requires navigation to be set.
    navigationStart: str | None = None
    # HTML injected after the last list item in the navigation list. Requires navigation to be set.
    navigationEnd: str | None = None


# All options available here:
# https://design-system.service.gov.uk/components/service-navigation/
class ServiceNavigationKwargs(BaseModel):
    # Classes to add to the service navigation container.
    classes: str | None = None
    # HTML attributes (for example, data attributes) to add to the service navigation container.
    attributes: dict[str, Any] | None = None
    # The text for the aria-label which labels the service navigation container when a service name is included.
    # Defaults to "Service information".
    ariaLabel: str | None = None
    # The text of the mobile navigation menu toggle.
    menuButtonText: str | None = None
    # The screen reader label for the mobile navigation menu toggle.
    # Defaults to the same value as menuButtonText if not specified.
    menuButtonLabel: str | None = None
    # The screen reader label for the mobile navigation menu.
    # Defaults to the same value as menuButtonText if not specified.
    navigationLabel: str | None = None
    # The ID used to associate the mobile navigation toggle with the navigation menu.
    # Defaults to navigation.
    navigationId: str | None = None
    # Classes to add to the navigation menu container.
    navigationClasses: str | None = None
    # The name of your service.
    serviceName: str | None = None
    # The homepage of your service.
    serviceUrl: str | None = None
    # Required. Used to add navigation to the service header.
    navigation: list[Navigation]
    # Specified points for injecting custom HTML into the service header.
    slots: Slots | None = None
