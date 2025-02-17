from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, TextOrHTMLMixin
from .error_message import ErrorMessageKwargs
from .fieldset import FieldsetKwargs


class RadioItemLabel(BaseModel):
    # Classes to add to the label tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the label tag.
    attributes: dict[str, Any] | None = None


class RadioItemConditional(BaseModel):
    # Required. The HTML to reveal when the radio is checked.
    html: str


class RadioItem(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within each radio item label.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within each radio item label.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Specific ID attribute for the radio item. If omitted, then idPrefix string will be applied.
    id: str | None = None
    # Required. Value for the radio input.
    value: str
    # Subset of options for the label used by each radio item within the radios component.
    label: RadioItemLabel | None = None
    # Can be used to add a hint to each radio item within the radios component.
    hint: InputHint | None = None
    # Divider text to separate radio items, for example the text "or".
    divider: str | None = None
    # Whether the radio should be checked when the page loads.
    # Takes precedence over the top-level value option.
    checked: bool | None = None
    # Provide additional content to reveal when the radio is checked.
    conditional: RadioItemConditional | None = None
    # If true, radio will be disabled.
    disabled: bool | None = None
    # HTML attributes (for example data attributes) to add to the radio input tag.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/radios/
class RadiosKwargs(BaseModel):
    # The fieldset used by the radios component.
    fieldset: FieldsetKwargs | None = None
    # Can be used to add a hint to the radios component.
    hint: InputHint | None = None
    # Can be used to add an error message to the radios component. The error message component will
    # not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the radios component.
    formGroup: FormGroup | None = None
    # Optional prefix. This is used to prefix the id attribute for each radio input, hint and error
    # message, separated by -. Defaults to the name option value.
    idPrefix: str | None = None
    # Required. Name attribute for the radio items.
    name: str
    # Required. The radio items within the radios component.
    items: list[RadioItem]
    # The value for the radio which should be checked when the page loads. Use this as an alternative to setting the checked option on each individual item.
    value: str | None = None
    # Classes to add to the radio container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the radio input tag.
    attributes: dict[str, Any] | None = None
