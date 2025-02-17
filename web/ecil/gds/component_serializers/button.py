from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/button/
class ButtonKwargs(TextOrHTMLMixin, BaseModel):
    # HTML element for the button component – input, button or a.
    # In most cases you will not need to set this as it will be configured automatically if href is provided.
    # This parameter will be removed in the next major version.
    element: str | None = None
    # Required. If html is set, this is not required.
    # Text for the input, button or a element.
    # If html is provided, the text option will be ignored and element will be automatically set
    # to "button" unless href is also set, or it has already been defined.
    text: str | None = None
    # Required. If text is set, this is not required. HTML for the button or a element only.
    # If html is provided, the text option will be ignored and element will be automatically set
    # to "button" unless href is also set, or it has already been defined.
    # This option has no effect if element is set to "input".
    html: str | None = None
    # Name for the input or button. This has no effect on a elements.
    name: str | None = None
    # Type for the input or button element – "button", "submit" or "reset".
    # Defaults to "submit". This has no effect on a elements.
    type: str | None = None
    # Value for the button element only. This has no effect on a or input elements.
    value: str | None = None
    # Whether the button component should be disabled. For input and button elements, disabled
    # and aria-disabled attributes will be set automatically. This has no effect on a elements.
    disabled: bool | None = None
    # The URL that the button component should link to. If this is set, element will be
    # automatically set to "a" if it has not already been defined.
    href: str | None = None
    # Classes to add to the button component.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the button component.
    attributes: dict[str, Any] | None = None
    # Prevent accidental double clicks on submit buttons from submitting forms multiple times.
    preventDoubleClick: bool | None = None
    # Use for the main call to action on your service’s start page.
    isStartButton: bool | None = None
    # The ID of the button.
    id: str | None = None
