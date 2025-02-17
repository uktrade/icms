from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, InputLabel
from .error_message import ErrorMessageKwargs


# All options available here:
# https://design-system.service.gov.uk/components/file-upload/
class FileUploadKwargs(BaseModel):
    # Required. The name of the input, which is submitted with the form data.
    name: str
    # Required. The ID of the input.
    id: str
    # Deprecated. Optional initial value of the input.
    value: str | None = None
    # If true, file input will be disabled.
    disabled: bool | None = None
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional
    # descriptive information for screenreader users.
    describedBy: str | None = None
    # Required. The label used by the file upload component.
    label: InputLabel
    # Can be used to add a hint to the file upload component.
    hint: InputHint | None = None
    # Can be used to add an error message to the file upload component.
    # The error message component will not display if you use a falsy value for errorMessage, for
    # example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # Additional options for the form group containing the file upload component.
    formGroup: FormGroup | None = None
    # Classes to add to the file upload component.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the file upload component.
    attributes: dict[str, Any] | None = None
