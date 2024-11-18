from typing import Any

from django import forms
from django.forms.utils import ErrorDict


class GDSFormMixin:
    # Used to display the gds error summary
    GDS_FORM = True

    # Extra type hints for clarity
    fields: list[forms.Field]
    errors: ErrorDict | None
    cleaned_data: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.gds_radio_conditional_fields: dict[str, str] = {}
        super().__init__(*args, **kwargs)

    def clean_radio_conditional_fields(
        self, radio_field_name: str, conditional_fields: list[str]
    ) -> None:
        """Checks that the conditional field is set if the radio field is set."""

        value = self.cleaned_data.get(radio_field_name)

        if not value:
            return

        # The value is the name of the conditional field
        if not self.cleaned_data.get(value):
            field_error = self.fields[value].error_messages["required"]
            self.add_error(  # type: ignore[attr-defined]
                value, forms.ValidationError(field_error, code="required")
            )

        # Remove any other conditional fields that may have been set previously.
        for field in conditional_fields:
            if field != value and self.cleaned_data.get(field):
                self.cleaned_data.pop(field)

    @property
    def error_summary_kwargs(self) -> dict[str, Any]:
        if not self.errors:
            return {}

        # TODO: Revisit in ECIL-325 to fix radio and checkbox input fields.
        return {
            "titleText": "There is a problem",
            "errorList": [
                {"text": error, "href": f"#id_{field_name}"}
                for field_name, error in self.errors.items()
            ],
        }
