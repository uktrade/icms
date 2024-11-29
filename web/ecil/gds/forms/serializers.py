from typing import Any, Self

from pydantic import BaseModel, Field, model_validator


class TextOrHTMLMixin:
    text: str | None
    html: str | None

    @model_validator(mode="after")
    def check_text_or_html_valid(self) -> Self:
        if self.text and self.html:
            raise ValueError("Only text or html can be entered")

        if not self.text and not self.html:
            raise ValueError("text or html must be entered")

        return self


class InputLabel(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the label. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the label. If html is provided, the text option will be ignored.
    html: str | None = None
    # The value of the for attribute, the ID of the input the label is associated with.
    label_for: str | None = Field(serialization_alias="for", default=None)
    # Whether the label also acts as the heading for the page.
    isPageHeading: bool | None = None
    # Classes to add to the label tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the label tag.
    attributes: dict[str, Any] | None = None


class InputHint(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the hint. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the hint. If html is provided, the text option will be ignored.
    html: str | None = None
    # Optional ID attribute to add to the hint span tag.
    id: str | None = None
    # Classes to add to the hint span tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the hint span tag.
    attributes: dict[str, Any] | None = None


class ErrorMessage(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required. Text to use within the error message. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required. HTML to use within the error message. If html is provided, the text option will be ignored.
    html: str | None = None
    # ID attribute to add to the error message <p> tag.
    id: str | None = None
    # Classes to add to the error message <p> tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the error message <p> tag.
    attributes: dict[str, Any] | None = None
    # A visually hidden prefix used before the error message. Defaults to "Error".
    visuallyHiddenText: str | None = None


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


class FieldsetLegend(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text to use within the legend.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML to use within the legend.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Classes to add to the legend.
    classes: str | None = None
    # Whether the legend also acts as the heading for the page.
    isPageHeading: bool | None = None


class Fieldset(BaseModel):
    # One or more element IDs to add to the aria-describedby attribute, used to provide additional descriptive information for screenreader users.
    describedBy: str | None = None
    # The legend for the fieldset component.
    legend: FieldsetLegend
    # Classes to add to the fieldset container.
    classes: str | None = None
    # Optional ARIA role attribute.
    role: str | None = None
    # HTML attributes (for example data attributes) to add to the fieldset container.
    attributes: dict[str, Any] | None = None
    # HTML to use/render within the fieldset element.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire fieldset component in a call block.
    caller: Any | None = None


class FormGroupBeforeInput(TextOrHTMLMixin, BaseModel):
    # Required. Text to add before the input. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. HTML to add before the input. If html is provided, the text option will be ignored.
    html: str | None = None


class FormGroupAfterInput(TextOrHTMLMixin, BaseModel):
    # Required. Text to add after the input. If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. HTML to add after the input. If html is provided, the text option will be ignored.
    html: str | None = None


class FormGroup(BaseModel):
    # Classes to add to the form group (for example to show error state for the whole group).
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the form group.
    attributes: dict[str, Any] | None = None
    # Content to add before the input used by the text input component.
    beforeInput: FormGroupBeforeInput | None = None
    # Content to add after the input used by the text input component.
    afterInput: FormGroupAfterInput | None = None


class InputWrapper(BaseModel):
    # Classes to add to the wrapping element.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the wrapping element.
    attributes: dict[str, Any] | None = None


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
    errorMessage: ErrorMessage | None = None
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


class CheckboxItemLabel(BaseModel):
    # Classes to add to the label tag.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the label tag.
    attributes: dict[str, Any] | None = None


class CheckboxItemConditional(BaseModel):
    html: str


class CheckboxItem(TextOrHTMLMixin, BaseModel):
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
    value: str
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


# All options available here:
# https://design-system.service.gov.uk/components/checkboxes/
class CheckboxesFieldKwargs(BaseModel):
    # One or more element IDs to add to the input aria-describedby attribute without a fieldset,
    # used to provide additional descriptive information for screenreader users.
    describedBy: str | None = None
    # Can be used to add a fieldset to the checkboxes component.
    fieldset: Fieldset | None = None
    # Can be used to add a hint to the checkboxes component.
    hint: InputHint | None = None
    # Can be used to add an error message to the checkboxes component. The error message component
    # will not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessage | None = None
    # Additional options for the form group containing the checkboxes component.
    formGroup: FormGroup | None = None
    # Optional prefix. This is used to prefix the id attribute for each checkbox item input, hint
    # and error message, separated by -. Defaults to the name option value.
    idPrefix: str | None = None
    # Required. Name attribute for all checkbox items.
    name: str
    # Required. The checkbox items within the checkboxes component.
    items: list[CheckboxItem]
    # Array of values for checkboxes which should be checked when the page loads.
    # Use this as an alternative to setting the checked option on each individual item.
    values: list[str] | None = None
    # Classes to add to the checkboxes container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the anchor tag.
    attributes: dict[str, Any] | None = None


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
    errorMessage: ErrorMessage | None = None
    # Additional options for the form group containing the date input component.
    formGroup: FormGroup | None = None
    # Can be used to add a fieldset to the date input component.
    fieldset: Fieldset | None = None
    # Classes to add to the date-input container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the date-input container.
    attributes: dict[str, Any] | None = None


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
    errorMessage: ErrorMessage | None = None
    # Additional options for the form group containing the file upload component.
    formGroup: FormGroup | None = None
    # Classes to add to the file upload component.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the file upload component.
    attributes: dict[str, Any] | None = None


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
    errorMessage: ErrorMessage | None = None
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
class RadioInputKwargs(BaseModel):
    # The fieldset used by the radios component.
    fieldset: Fieldset | None = None
    # Can be used to add a hint to the radios component.
    hint: InputHint | None = None
    # Can be used to add an error message to the radios component. The error message component will
    # not display if you use a falsy value for errorMessage, for example false or null.
    errorMessage: ErrorMessage | None = None
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


class SelectItem(BaseModel):
    # Value for the option. If this is omitted, the value is taken from the text content of the option element.
    value: str | None = None
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
class SelectFieldKwargs(BaseModel):
    # Required. ID for each select box.
    id: str
    # Required. Name property for the select.
    name: str
    # Required. The items within the select component.
    items: list[SelectItem]
    # Value for the option which should be selected.
    # Use this as an alternative to setting the selected option on each individual item.
    value: str | None = None
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
    errorMessage: ErrorMessage | None = None
    # Additional options for the form group containing the select component.
    formGroup: FormGroup | None = None
    # Classes to add to the select.
    classes: str | None = None
    # object 	HTML attributes (for example data attributes) to add to the select.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/textarea/
class TextareaFieldKwargs(BaseModel):
    # Required. The ID of the textarea.
    id: str
    # Required. The name of the textarea, which is submitted with the form data.
    name: str
    # Optional field to enable or disable the spellcheck attribute on the textarea.
    spellcheck: bool | None = None
    # Optional number of textarea rows (default is 5 rows).
    rows: str | None = None
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
    errorMessage: ErrorMessage | None = None
    # Additional options for the form group containing the textarea component.
    formGroup: FormGroup | None = None
    # Classes to add to the textarea.
    classes: str | None = None
    # Attribute to identify input purpose, for example "street-address".
    # See autofill for full list of attributes that can be used.
    autocomplete: str | None = None
    # HTML attributes (for example data attributes) to add to the textarea.
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
    errorMessage: ErrorMessage | None = None
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
