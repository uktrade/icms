from typing import Any

from django.forms.models import ModelChoiceIteratorValue
from pydantic import BaseModel, ConfigDict

from .common import FormGroup, InputHint, InputLabel
from .error_message import ErrorMessageKwargs


class SelectItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Value for the option. If this is omitted, the value is taken from the text content of the option element.
    value: str | int | None | ModelChoiceIteratorValue = None
    # Required. Text for the option item.
    text: str
    # Whether the option should be selected when the page loads. Takes precedence over the top-level value option.
    selected: bool | None = None
    # Sets the option item as disabled.
    disabled: bool | None = None
    # HTML attributes (for example data attributes) to add to the option.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/select/
class SelectKwargs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Required. ID for each select box.
    id: str
    # Required. Name property for the select.
    name: str
    # Required. The items within the select component.
    items: list[SelectItem]
    # Value for the option which should be selected.
    # Use this as an alternative to setting the selected option on each individual item.
    value: str | int | None | ModelChoiceIteratorValue = None
    # If true, select box will be disabled. Use the disabled option on each individual item to only
    # disable certain options.
    disabled: bool | None = None
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional
    # descriptive information for screenreader users.
    describedBy: str | None = None
    # Required. The label used by the select component.
    label: InputLabel
    # Can be used to add a hint to the select component.
    hint: InputHint | None = None
    # Can be used to add an error message to the select component. The error message component will
    # not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the select component.
    formGroup: FormGroup | None = None
    # Classes to add to the select.
    classes: str | None = None
    # object 	HTML attributes (for example data attributes) to add to the select.
    attributes: dict[str, Any] | None = None
