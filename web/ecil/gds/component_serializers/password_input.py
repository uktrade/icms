from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, InputLabel
from .error_message import ErrorMessageKwargs


class PasswordButton(BaseModel):
    # Classes to add to the button.
    classes: str


# All options available here:
# https://design-system.service.gov.uk/components/password-input/
class PasswordInputKwargs(BaseModel):
    # Required. The ID of the input.
    id: str
    # Required. The name of the input, which is submitted with the form data.
    name: str
    # Optional initial value of the input.
    value: str | None = None
    # If true, input will be disabled.
    disabled: bool | None = None
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional
    # descriptive information for screenreader users.
    describedBy: str | None = None
    # Required. The label used by the text input component.
    label: InputLabel
    # Can be used to add a hint to a text input component.
    hint: InputHint | None = None
    # Can be used to add an error message to the text input component. The error message component
    # will not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the text input component.
    formGroup: FormGroup | None = None
    # Classes to add to the input.
    classes: str | None = None
    # Attribute to identify input purpose. See autofill for full list of values that can be used.
    # Default is "current-password".
    autocomplete: str | None = None
    # HTML attributes (for example data attributes) to add to the input.
    attributes: dict[str, Any] | None = None
    # Button text when the password is hidden. Defaults to "Show".
    showPasswordText: str | None = None
    # Button text when the password is visible. Defaults to "Hide".
    hidePasswordText: str | None = None
    # Button text exposed to assistive technologies, like screen readers, when the password is hidden.
    # Defaults to "Show password".
    showPasswordAriaLabelText: str | None = None
    # Button text exposed to assistive technologies, like screen readers, when the password is visible.
    # Defaults to "Hide password".
    hidePasswordAriaLabelText: str | None = None
    # Announcement made to screen reader users when their password has become visible in plain text.
    # Defaults to "Your password is visible".
    passwordShownAnnouncementText: str | None = None
    # Announcement made to screen reader users when their password has been obscured and is not visible.
    # Defaults to "Your password is hidden".
    passwordHiddenAnnouncementText: str | None = None
    # Optional object allowing customisation of the toggle button.
    button: PasswordButton | None = None
