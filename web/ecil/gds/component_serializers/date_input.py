from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint
from .error_message import ErrorMessageKwargs
from .fieldset import FieldsetKwargs


class DateItem(BaseModel):
    # Item-specific ID. If provided, it will be used instead of the generated ID.
    id: str | None = None
    # Required. Item-specific name attribute.
    name: str
    # Item-specific label text. If provided, this will be used instead of name for item label text.
    label: str | None = None
    # If provided, it will be used as the initial value of the input.
    value: str | None = None
    # Attribute to identify input purpose, for instance "bday-day".
    # See autofill for full list of attributes that can be used.
    autocomplete: str | None = None
    # Attribute to provide a regular expression pattern, used to match allowed character
    # combinations for the input value.
    pattern: str | None = None
    # classes 	string 	Classes to add to date input item.
    classes: str | None = None
    # attributes 	object 	HTML attributes (for example data attributes) to add to the date input tag.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/date-input/
class DateInputKwargs(BaseModel):
    # Required. This is used for the main component and to compose the ID attribute for each item.
    id: str
    # Optional prefix. This is used to prefix each item name, separated by -.
    namePrefix: str | None = None
    # items 	array 	The inputs within the date input component
    items: list[DateItem]
    # Can be used to add a hint to a date input component.
    hint: InputHint | None = None
    # Can be used to add an error message to the date input component.
    # The error message component will not display if you use a falsy value for errorMessage, for
    # example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the date input component.
    formGroup: FormGroup | None = None
    # Can be used to add a fieldset to the date input component.
    fieldset: FieldsetKwargs | None = None
    # Classes to add to the date-input container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the date-input container.
    attributes: dict[str, Any] | None = None
