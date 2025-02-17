from typing import Any

from pydantic import BaseModel

from .common import FormGroup, InputHint, InputLabel
from .error_message import ErrorMessageKwargs


class CountMessage(BaseModel):
    # Classes to add to the count message.
    classes: str


# All options available here:
# https://design-system.service.gov.uk/components/character-count/
class CharacterCountKwargs(BaseModel):
    # Required. The ID of the textarea.
    id: str
    # Required. The name of the textarea, which is submitted with the form data.
    name: str
    # Optional number of textarea rows (default is 5 rows).
    rows: str | None = None
    # Optional initial value of the textarea.
    value: str | None = None
    # Required. If maxwords is set, this is not required. The maximum number of characters. If maxwords is provided, the maxlength option will be ignored.
    maxlength: str | None = None
    # Required. If maxlength is set, this is not required. The maximum number of words. If maxwords is provided, the maxlength option will be ignored.
    maxwords: str | None = None
    # The percentage value of the limit at which point the count message is displayed. If this attribute is set, the count message will be hidden by default.
    threshold: str | None = None
    # Required. The label used by the character count component.
    label: InputLabel
    # Can be used to add a hint to the character count component.
    hint: InputHint | None = None
    # Can be used to add an error message to the character count component. The error message
    # component will not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessageKwargs | None = None
    # formGroup 	object 	Additional options for the form group containing the character count component.
    formGroup: FormGroup | None = None
    # Classes to add to the textarea.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the textarea.
    attributes: dict[str, Any] | None = None
    # Optional field to enable or disable the spellcheck attribute on the character count.
    spellcheck: bool | None = None
    # Additional options for the count message used by the character count component.
    countMessage: CountMessage | None = None
    # Message made available to assistive technologies to describe that the component accepts only a
    # limited amount of content. It is visible on the page when JavaScript is unavailable. The
    # component will replace the %{count} placeholder with the value of the maxlength or maxwords
    # parameter.
    textareaDescriptionText: str | None = None
    # TODO: Type the pluralised list of messages type (currently dict[str, str])
    #       https://frontend.design-system.service.gov.uk/localise-govuk-frontend/
    # Message displayed when the number of characters is under the configured maximum, maxlength.
    # This message is displayed visually and through assistive technologies.
    # The component will replace the %{count} placeholder with the number of remaining characters.
    # This is a pluralised list of messages.
    charactersUnderLimitText: dict[str, str] | None = None
    # Message displayed when the number of characters reaches the configured maximum, maxlength.
    # This message is displayed visually and through assistive technologies.
    charactersAtLimitText: str | None = None
    # Message displayed when the number of characters is over the configured maximum, maxlength.
    # This message is displayed visually and through assistive technologies.
    # The component will replace the %{count} placeholder with the number of characters above the maximum.
    # This is a pluralised list of messages.
    charactersOverLimitText: dict[str, str] | None = None
    # Message displayed when the number of words is under the configured maximum, maxwords.
    # This message is displayed visually and through assistive technologies.
    # The component will replace the %{count} placeholder with the number of remaining words.
    # This is a pluralised list of messages.
    wordsUnderLimitText: dict[str, str] | None = None
    # Message displayed when the number of words reaches the configured maximum, maxwords.
    # This message is displayed visually and through assistive technologies.
    wordsAtLimitText: str | None = None
    # Message displayed when the number of words is over the configured maximum, maxwords.
    # This message is displayed visually and through assistive technologies.
    # The component will replace the %{count} placeholder with the number of characters above the maximum.
    # This is a pluralised list of messages.
    wordsOverLimitText: dict[str, str] | None = None
