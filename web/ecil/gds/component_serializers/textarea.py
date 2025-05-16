from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, InputLabel
from .error_message import ErrorMessageKwargs


# All options available here:
# https://design-system.service.gov.uk/components/textarea/
class TextareaKwargs(BaseModel):
    # Required. The ID of the textarea.
    id: str
    # Required. The name of the textarea, which is submitted with the form data.
    name: str
    # Optional field to enable or disable the spellcheck attribute on the textarea.
    spellcheck: bool | None = None
    # Optional number of textarea rows (default is 5 rows).
    rows: str | int | None = None
    # Optional initial value of the textarea.
    value: str | None = None
    # If true, textarea will be disabled.
    disabled: bool | None = None
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional
    # descriptive information for screenreader users.
    describedBy: str | None = None
    # Required. The label used by the textarea component.
    label: InputLabel
    # Can be used to add a hint to the textarea component.
    hint: InputHint | None = None
    # Can be used to add an error message to the textarea component. The error message component
    # will not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the textarea component.
    formGroup: FormGroup | None = None
    # Classes to add to the textarea.
    classes: str | None = None
    # Attribute to identify input purpose, for example "street-address".
    # See autofill for full list of attributes that can be used.
    autocomplete: str | None = None
    # HTML attributes (for example data attributes) to add to the textarea.
    attributes: dict[str, Any] | None = None
