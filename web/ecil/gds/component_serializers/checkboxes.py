from typing import Any

from django.forms.models import ModelChoiceIteratorValue
from pydantic import BaseModel, ConfigDict

from .common import FormGroup, InputHint, TextOrHTMLMixin
from .error_message import ErrorMessageKwargs
from .fieldset import FieldsetKwargs


class CheckboxItemLabel(BaseModel):
    # Classes to add to the label tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the label tag.
    attributes: dict[str, Any] | None = None


class CheckboxItemConditional(BaseModel):
    html: str


class CheckboxItem(TextOrHTMLMixin, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # If html is set, this is not required. Text to use within each checkbox item label.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # If text is set, this is not required. HTML to use within each checkbox item label.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Specific ID attribute for the checkbox item. If omitted, then component global idPrefix
    # option will be applied.
    id: str | None = None
    # Specific name for the checkbox item. If omitted, then component global name string will be applied.
    name: str | None = None
    # Required. Value for the checkbox input.
    value: str | int | ModelChoiceIteratorValue
    # Subset of options for the label used by each checkbox item within the checkboxes component.
    label: CheckboxItemLabel | None = None
    # Can be used to add a hint to each checkbox item within the checkboxes component.
    hint: InputHint | None = None
    # Divider text to separate checkbox items, for example the text "or".
    divider: str | None = None
    # Whether the checkbox should be checked when the page loads. Takes precedence over the top-level values option.
    checked: bool | None = None
    # Provide additional content to reveal when the checkbox is checked.
    conditional: CheckboxItemConditional | None = None
    # If set to "exclusive", implements a ‘None of these’ type behaviour via JavaScript when checkboxes are clicked.
    behaviour: str | None = None
    # If true, checkbox will be disabled.
    disabled: bool | None = None
    # HTML attributes (for example data attributes) to add to the checkbox input tag.
    attributes: dict[str, Any] | None = None


class CheckboxItemDivider(BaseModel):
    divider: str


# All options available here:
# https://design-system.service.gov.uk/components/checkboxes/
class CheckboxesKwargs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # One or more element IDs to add to the input aria-describedby attribute without a fieldset,
    # used to provide additional descriptive information for screenreader users.
    describedBy: str | None = None
    # Can be used to add a fieldset to the checkboxes component.
    fieldset: FieldsetKwargs | None = None
    # Can be used to add a hint to the checkboxes component.
    hint: InputHint | None = None
    # Can be used to add an error message to the checkboxes component. The error message component
    # will not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the checkboxes component.
    formGroup: FormGroup | None = None
    # Optional prefix. This is used to prefix the id attribute for each checkbox item input, hint
    # and error message, separated by -. Defaults to the name option value.
    idPrefix: str | None = None
    # Required. Name attribute for all checkbox items.
    name: str
    # Required. The checkbox items within the checkboxes component.
    items: list[CheckboxItem | CheckboxItemDivider]
    # Array of values for checkboxes which should be checked when the page loads.
    # Use this as an alternative to setting the checked option on each individual item.
    values: list[str | int | ModelChoiceIteratorValue] | None = None
    # Classes to add to the checkboxes container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the anchor tag.
    attributes: dict[str, Any] | None = None
