import datetime as dt
from decimal import Decimal
from typing import Any, ClassVar

from django import forms
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

    def __init__(self, *args, **kwargs):
        fields = (forms.CharField(), forms.CharField(), forms.CharField())
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

    def compress(self, data_list: list[str]) -> dt.date | None:
        day, month, year = data_list
        if day and month and year:
            if len(year) == 2:
                year = f"20{year}"

            if len(year) < 4:
                raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

            try:
                return dt.date(day=int(day), month=int(month), year=int(year))
            except ValueError:
                raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
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
