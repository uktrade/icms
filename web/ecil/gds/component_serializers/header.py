from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Navigation(TextOrHTMLMixin, BaseModel):
    # Required. Text for the navigation item. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. HTML for the navigation item. If html is provided, the text option will be ignored.
    html: str | None = None
    # URL of the navigation item anchor.
    href: str | None = None
    # Flag to mark the navigation item as active or not.
    active: bool
    # HTML attributes (for example data attributes) to add to the navigation item anchor.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/header/
class GovUKHeaderKwargs(BaseModel):
    # The URL of the homepage. Defaults to "/".
    homepageUrl: str | None = None
    # Product name, used when the product name follows on directly from ‘GOV.UK’.
    # For example, GOV.UK Pay or GOV.UK Design System.
    # In most circumstances, you should use serviceName.
    productName: str | None = None
    # The name of your service, included in the header.
    serviceName: str | None = None
    # URL for the service name anchor.
    serviceUrl: str | None = None
    # Can be used to add navigation to the header component.
    navigation: list[Navigation]
    # Classes for the navigation section of the header.
    navigationClasses: str
    # Text for the aria-label attribute of the navigation.
    # Defaults to the same value as menuButtonText.
    navigationLabel: str
    # Text for the aria-label attribute of the button that opens the mobile navigation, if there is a mobile navigation menu.
    menuButtonLabel: str
    # Text of the button that opens the mobile navigation menu, if there is a mobile navigation menu.
    # There is no enforced character limit, but there is a limited display space so keep text as short as possible.
    # By default, this is set to ‘Menu’.
    menuButtonText: str
    # Classes for the container, useful if you want to make the header fixed width.
    containerClasses: str
    # Classes to add to the header container.
    classes: str
    # HTML attributes (for example data attributes) to add to the header container.
    attributes: dict[str, Any] | None = None
    # Deprecated. If true, uses the Tudor crown from King Charles III’s royal cypher.
    # Otherwise, uses the St. Edward’s crown. Default is true.
    useTudorCrown: bool | None = None
