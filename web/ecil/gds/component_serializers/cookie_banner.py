from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class Action(BaseModel):
    # Required. The button or link text.
    text: str
    # The type of button – "button" or "submit".
    # If href is provided, set type to "button" render a link styled as a button.
    type: str | None = None
    # The href for a link. Set type to "button" and set href to render a link styled as a button.
    href: str | None = None
    # The name attribute for the button. Does not apply if you set href, which makes a link.
    name: str | None = None
    # The value attribute for the button. Does not apply if you set href, which makes a link.
    value: str
    # The additional classes that you want to add to the button or link.
    classes: str
    # The additional attributes that you want to add to the button or link. For example, data attributes.
    attributes: dict[str, Any] | None = None


class Message(TextOrHTMLMixin, BaseModel):
    # The heading text that displays in the message.
    # You can use any string with this option.
    # If you set headingHtml, headingText is ignored.
    headingText: str | None = None
    # The heading HTML to use within the message.
    # You can use any string with this option.
    # If you set headingHtml, headingText is ignored.
    # If you are not passing HTML, use headingText.
    headingHtml: str | None = None
    # Required. The text for the main content within the message.
    # You can use any string with this option. If you set html, text is not required and is ignored.
    text: str | None = None
    # Required. The HTML for the main content within the message.
    # You can use any string with this option. If you set html, text is not required and is ignored.
    # If you are not passing HTML, use text.
    html: str | None = None
    # The buttons and links that you want to display in the message.
    # actions defaults to "button" unless you set href, which renders the action as a link.
    actions: list[Action]
    # Defaults to false. If you set it to true, the message is hidden.
    # You can use hidden for client-side implementations where the confirmation message HTML is present, but hidden on the page.
    hidden: bool | None = None
    # Set role to "alert" on confirmation messages to allow assistive tech to automatically read the message.
    # You will also need to move focus to the confirmation message using JavaScript you have written yourself.
    role: str | None = None
    # The additional classes that you want to add to the message.
    classes: str | None = None
    # The additional attributes that you want to add to the message. For example, data attributes.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/cookie-banner/
class CookieBannerKwargs(BaseModel):
    # The text for the aria-label which labels the cookie banner region.
    # This region applies to all messages that the cookie banner includes.
    # For example, the cookie message and the confirmation message.
    # Defaults to "Cookie banner".
    ariaLabel: str | None = None
    # Defaults to false.
    # If you set this option to true, the whole cookie banner is hidden, including all messages within the banner.
    # You can use hidden for client-side implementations where the cookie banner HTML is present,
    # but hidden until the cookie banner is shown using JavaScript.
    hidden: bool | None = None
    # The additional classes that you want to add to the cookie banner.
    classes: str | None = None
    # The additional attributes that you want to add to the cookie banner. For example, data attributes.
    attributes: dict[str, Any] | None = None
    # Required. The different messages you can pass into the cookie banner. For example, the cookie message and the confirmation message.
    messages: list[Message]
