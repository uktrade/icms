from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, InputLabel, TextOrHTMLMixin
from .error_message import ErrorMessageKwargs


class InputPrefix(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the prefix. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the prefix. If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the prefix.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the prefix element.
    attributes: dict[str, Any] | None = None


class InputSuffix(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the suffix. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the suffix. If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the suffix element.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the suffix element.
    attributes: dict[str, Any] | None = None


class InputWrapper(BaseModel):
    # Classes to add to the wrapping element.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the wrapping element.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/text-input/
class TextInputKwargs(BaseModel):
    # Required. The ID of the input.
    id: str
    # Required. The name of the input, which is submitted with the form data.
    name: str
    # Type of input control to render, for example, a password input control. Defaults to "text".
    type: str | None = None
    # Optional value for inputmode.
    inputmode: str | None = None
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
    # Can be used to add a prefix to the text input component.
    prefix: InputPrefix | None = None
    # Can be used to add a suffix to the text input component.
    suffix: InputSuffix | None = None
    # Additional options for the form group containing the text input component.
    formGroup: FormGroup | None = None
    # Classes to add to the input.
    classes: str | None = None
    # Attribute to identify input purpose, for instance “postal-code” or “username”.
    autocomplete: str | None = None
    # Attribute to provide a regular expression pattern, used to match allowed character combinations for the input value.
    pattern: str | None = None
    # Optional field to enable or disable the spellcheck attribute on the input.
    spellcheck: bool | None = None
    # Optional field to enable or disable autocapitalisation of user input. See autocapitalization for a full list of values that can be used.
    autocapitalize: str | None = None
    # If any of prefix, suffix, formGroup.beforeInput or formGroup.afterInput have a value, a
    # wrapping element is added around the input and inserted content. This object allows you to
    # customise that wrapping element.
    inputWrapper: InputWrapper | None = None
    # HTML attributes (for example data attributes) to add to the input.
    attributes: dict[str, Any] | None = None
