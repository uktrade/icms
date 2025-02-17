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
