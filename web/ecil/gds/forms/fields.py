import datetime as dt
from decimal import Decimal
from typing import Any, ClassVar

from django import forms
from django.core.validators import RegexValidator
from jinja2.filters import do_mark_safe

from web.domains.file.utils import ICMSFileField

from .validators import MaxWordsValidator


class GDSMixin:
    # Field template name
    template_name: ClassVar[str | None] = None
    # BoundField class that defines Nunjucks context
    BF: ClassVar[type[forms.BoundField]]

    def __init__(self, *args: Any, radio_conditional: bool = False, **kwargs: Any) -> None:
        """Mixin class for all GDS form fields

        :param radio_conditional: Set True to indicate this field is for a GovUKRadioInputField field.
        """
        self.radio_conditional = radio_conditional

        # All radio_conditional fields are optional
        if self.radio_conditional:
            kwargs["required"] = False

        # Optional template name that can be defined on field class.
        if self.template_name:
            kwargs["template_name"] = self.template_name

        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        return self.BF(form, self, field_name)


class GovUKCharacterCountField(GDSMixin, forms.CharField):
    def __init__(
        self, *args: Any, max_length: int | None = None, max_words: int | None = None, **kwargs: Any
    ) -> None:

        if not max_length and not max_words:
            raise ValueError("You must specify either a max_length or max_words value.")

        if max_length and max_words:
            raise ValueError("You must only specify either a max_length or max_words value.")

        self.max_length = max_length
        self.max_words = max_words

        # Pass max_length to kwargs (as it's a CharField kwarg that gets set as a html attribute)
        if max_length:
            kwargs["max_length"] = max_length

        super().__init__(*args, **kwargs)

        if max_words is not None:
            self.validators.append(MaxWordsValidator(max_words))

    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/character-count/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                # TODO: ECIL-323 Remove `or ""` after ECIL-323 is fixed.
                "value": self.value() or "",
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            if self.field.max_length:
                context["gds_kwargs"]["maxlength"] = self.field.max_length

            if self.field.max_words:
                context["gds_kwargs"]["maxwords"] = self.field.max_words

            return context


class GovUKCheckboxesField(GDSMixin, forms.MultipleChoiceField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            items = [{"value": value, "text": label} for value, label in self.field.choices]

            # All options available here:
            # https://design-system.service.gov.uk/components/checkboxes/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "fieldset": {
                    "legend": {
                        "text": self.label,
                        "isPageHeading": True,
                        "classes": "govuk-fieldset__legend--l",
                    }
                },
                "hint": {"text": self.help_text} if self.help_text else None,
                "values": self.data or self.initial or [],
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
                "items": items,
            }

            return context


class DateMultiWidget(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, widgets=[forms.TextInput(), forms.TextInput(), forms.TextInput()], **kwargs
        )

    def decompress(self, value):
        """
        Convert a ``date`` into values for the day, month and year so it can be
        displayed in the widget's fields.

        Args:
            value (date): the date to be displayed

        Returns:
            a 3-tuple containing the day, month and year components of the date.

        """

        if value:
            return value.day, value.month, value.year
        return None, None, None


class GovUKDateInputField(GDSMixin, forms.MultiValueField):
    widget = DateMultiWidget

    default_error_messages = {
        "required": "Enter the day, month and year",
        "incomplete": "Enter the day, month and year",
    }

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(
                error_messages={"incomplete": "Enter the day of the month"},
                validators=[RegexValidator(r"^[0-9]+$", "Enter a valid day")],
            ),
            forms.CharField(
                error_messages={"incomplete": "Enter the month"},
                validators=[RegexValidator(r"^[0-9]+$", "Enter a valid month")],
            ),
            forms.CharField(
                error_messages={"incomplete": "Enter the year"},
                validators=[RegexValidator(r"^[0-9]+$", "Enter a valid year")],
            ),
        )

        super().__init__(fields, *args, **kwargs)

    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            items = [
                {"label": "Day", "name": f"{self.name}_0"},
                {"label": "Month", "name": f"{self.name}_1"},
                {"label": "Year", "name": f"{self.name}_2"},
            ]

            value = self.value()
            if not isinstance(value, list):
                value = self.field.widget.decompress(value)

            for i, val in enumerate(value):
                items[i]["value"] = val

            # All options available here:
            # https://design-system.service.gov.uk/components/date-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                # "namePrefix": self.name,
                "fieldset": {
                    "legend": {
                        "text": self.label,
                        "isPageHeading": True,
                        "classes": "govuk-fieldset__legend--l",
                    }
                },
                "hint": {"text": self.help_text} if self.help_text else None,
                "items": items,
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context

    # Copied from here:
    # https://github.com/wildfish/crispy-forms-gds/blob/master/src/crispy_forms_gds/fields.py
    def clean(self, value: list | tuple) -> dt.date | None:
        clean_data = []
        errors = []
        if self.disabled and not isinstance(value, list):
            value = self.widget.decompress(value)  # type:ignore

        if not value or isinstance(value, (list, tuple)):
            if not value or not [v for v in value if v not in self.empty_values]:
                if self.required:
                    raise forms.ValidationError(self.error_messages["required"], code="required")
                else:
                    return self.compress([None, None, None])
        else:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

        for i, field in enumerate(self.fields):
            field.widget.errors = []
            try:
                field_value = value[i]
            except IndexError:
                field_value = None
            if field_value in self.empty_values:
                if self.require_all_fields:
                    # Raise a 'required' error if the MultiValueField is
                    # required and any field is empty.
                    if self.required:
                        raise forms.ValidationError(
                            self.error_messages["required"], code="required"
                        )
                elif field.required:
                    # Otherwise, add an 'incomplete' error to the list of
                    # collected errors and skip field cleaning, if a required
                    # field is empty.
                    if field.error_messages["incomplete"] not in errors:
                        errors.append(field.error_messages["incomplete"])
                        field.widget.errors.append(field.error_messages["incomplete"])
                    continue
            try:
                clean_data.append(field.clean(field_value))
            except forms.ValidationError as e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter. Skip duplicates.
                errors.extend(m for m in e.error_list if m not in errors)
                field.widget.errors.extend(m for m in e.messages if m not in field.widget.errors)
        if errors:
            raise forms.ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list: list[str | None]) -> dt.date | None:
        """Convert the values entered into the fields as a ``date``.

        :param data_list: A 3 element list of values entered into the fields.
        """

        day, month, year = data_list
        if day and month and year:
            try:
                return dt.date(day=int(day), month=int(month), year=int(year))
            except ValueError as e:
                raise forms.ValidationError(str(e)) from e
        else:
            return None


class GovUKDecimalField(GDSMixin, forms.DecimalField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            number_attrs = {
                # Taken from forms.DecimalField
                "step": str(Decimal(1).scaleb(-self.field.decimal_places)).lower(),
            }

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "type": "number",
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs | number_attrs,
            }

            return context


class GovUKEmailField(GDSMixin, forms.EmailField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "type": "email",
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKFileUploadField(GDSMixin, ICMSFileField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/file-upload/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": do_mark_safe(self.help_text)} if self.help_text else None,
            }

            return context


class GovUKFloatField(GDSMixin, forms.FloatField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "type": "number",
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKIntegerField(GDSMixin, forms.IntegerField):
    """Custom field using django IntegerField validation and rendering a gds text-input."""

    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "type": "number",
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKPasswordInputField(GDSMixin, forms.CharField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/password-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKRadioInputField(GDSMixin, forms.ChoiceField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            items = []
            for value, label in self.field.choices:
                item = {"value": value, "text": label}
                if value in self.form.gds_radio_conditional_fields:
                    item["conditional"] = {"html": self.form.gds_radio_conditional_fields[value]}

                items.append(item)

            # All options available here:
            # https://design-system.service.gov.uk/components/password-input/
            context["gds_kwargs"] = {
                "name": self.name,
                "fieldset": {
                    "legend": {
                        "text": self.label,
                        "isPageHeading": True,
                        "classes": "govuk-fieldset__legend--l",
                    }
                },
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "items": items,
            }

            return context


class GovUKSelectField(GDSMixin, forms.ChoiceField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            items = [{"value": value, "text": label} for value, label in self.field.choices]

            # All options available here:
            # https://design-system.service.gov.uk/components/select/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
                "items": items,
            }

            return context


class GovUKSlugField(GDSMixin, forms.SlugField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKTextareaField(GDSMixin, forms.CharField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/textarea/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                # TODO: ECIL-323 Remove `or ""` after ECIL-323 is fixed.
                "value": self.value() or "",
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context


class GovUKTextInputField(GDSMixin, forms.CharField):
    class BF(forms.BoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            # All options available here:
            # https://design-system.service.gov.uk/components/text-input/
            context["gds_kwargs"] = {
                "id": self.auto_id,
                "name": self.name,
                "label": {"text": self.label, "classes": "govuk-label--l", "isPageHeading": True},
                "hint": {"text": self.help_text} if self.help_text else None,
                "value": self.value(),
                "errorMessage": {"text": " ".join(self.errors)} if self.errors else None,
                "attributes": self.field.widget.attrs,
            }

            return context
