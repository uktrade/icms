from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/exit-this-page/
class ExitThisPageKwargs(TextOrHTMLMixin, BaseModel):
    # Text for the link. If html is provided, the text option will be ignored.
    # Defaults to "Emergency Exit this page" with ‘Emergency’ visually hidden.
    text: str | None = None
    # HTML for the link. If html is provided, the text option will be ignored.
    # Defaults to "Emergency Exit this page" with ‘Emergency’ visually hidden.
    html: str | None = None
    # URL to redirect the current tab to. Defaults to "https://www.bbc.co.uk/weather".
    redirectUrl: str | None = None
    # ID attribute to add to the exit this page container.
    id: str | None = None
    # Classes to add to the exit this page container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the exit this page container.
    attributes: dict[str, Any] | None = None
    # Text announced by screen readers when Exit this Page has been activated via the keyboard shortcut.
    # Defaults to "Loading.".
    activatedText: str | None = None
    # Text announced by screen readers when the keyboard shortcut has timed out without successful activation.
    # Defaults to "Exit this page expired.".
    timedOutText: str | None = None
    # Text announced by screen readers when the user must press Shift two more times to activate the button.
    # Defaults to "Shift, press 2 more times to exit.".
    pressTwoMoreTimesText: str | None = None
    # Text announced by screen readers when the user must press Shift one more time to activate the button.
    # Defaults to "Shift, press 1 more time to exit.".
    pressOneMoreTimeText: str | None = None
