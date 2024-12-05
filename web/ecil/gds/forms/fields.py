import datetime as dt
from decimal import Decimal
from typing import Any, ClassVar

from django import forms
from django.core.validators import RegexValidator
from jinja2.filters import do_mark_safe

from web.domains.file.utils import ICMSFileField

from . import serializers
from .validators import MaxWordsValidator


class GDSFieldMixin:
    # Field template name
    template_name: ClassVar[str | None] = None
    # BoundField class that defines Nunjucks context
    BF: ClassVar[type[forms.BoundField]]

    def get_overrides(self) -> dict[str, Any]:
        return {}

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


class GDSBoundField(forms.BoundField):
    def _get_label(self) -> serializers.InputLabel:
        return serializers.InputLabel(
            text=self.label,
            isPageHeading=True,
            classes="govuk-label--l",
        )

    def _get_hint(self) -> serializers.InputHint | None:
        if not self.help_text:
            return None

        return serializers.InputHint(
            text=self.help_text,
        )

    def _get_errors(self) -> serializers.ErrorMessage | None:
        if not self.errors:
            return None

        return serializers.ErrorMessage(text=" ".join(self.errors))


class GovUKCharacterCountField(GDSFieldMixin, forms.CharField):
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

    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.CharacterCountKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                # TODO: ECIL-323 Remove `or ""` after ECIL-323 is fixed.
                value=self.value() or "",
                maxlength=str(self.field.max_length) if self.field.max_length else None,
                maxwords=str(self.field.max_words) if self.field.max_words else None,
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )
            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKCheckboxesField(GDSFieldMixin, forms.MultipleChoiceField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.CheckboxesFieldKwargs(
                name=self.name,
                fieldset=serializers.Fieldset(
                    legend=serializers.FieldsetLegend(
                        text=self.label,
                        isPageHeading=True,
                        classes="govuk-fieldset__legend--l",
                    )
                ),
                hint=self._get_hint(),
                items=[
                    serializers.CheckboxItem(id=f"{self.auto_id}_{i}", value=value, text=label)
                    for i, (value, label) in enumerate(self.field.choices)
                ],
                values=self.data or self.initial or [],
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )
            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

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


class GovUKDateInputField(GDSFieldMixin, forms.MultiValueField):
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

    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            value = self.value()
            if not isinstance(value, list):
                value = self.field.widget.decompress(value)

            serializer = serializers.DateInputKwargs(
                id=self.auto_id,
                fieldset=serializers.Fieldset(
                    legend=serializers.FieldsetLegend(
                        text=self.label, isPageHeading=True, classes="govuk-fieldset__legend--l"
                    )
                ),
                hint=self._get_hint(),
                items=[
                    serializers.DateItem(
                        label="Day", name=f"{self.name}_0", value=value[0], id=f"{self.auto_id}_0"
                    ),
                    serializers.DateItem(
                        label="Month", name=f"{self.name}_1", value=value[1], id=f"{self.auto_id}_1"
                    ),
                    serializers.DateItem(
                        label="Year", name=f"{self.name}_2", value=value[2], id=f"{self.auto_id}_2"
                    ),
                ],
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )
            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

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


class GovUKDecimalField(GDSFieldMixin, forms.DecimalField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            number_attrs = {
                # Taken from forms.DecimalField
                "step": str(Decimal(1).scaleb(-self.field.decimal_places)).lower(),
            }

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                type="number",
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs | number_attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKEmailField(GDSFieldMixin, forms.EmailField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                type="email",
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKFileUploadField(GDSFieldMixin, ICMSFileField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.FileUploadKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                errorMessage=self._get_errors(),
                **self.field.get_overrides(),
            )

            gds_kwargs = serializer.model_dump(exclude_defaults=True)

            # The hint contains HTML so do_mark_safe after model_dump
            if gds_kwargs.get("hint"):
                gds_kwargs["hint"]["text"] = do_mark_safe(gds_kwargs["hint"]["text"])

            context["gds_kwargs"] = gds_kwargs

            return context


class GovUKFloatField(GDSFieldMixin, forms.FloatField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                type="number",
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKIntegerField(GDSFieldMixin, forms.IntegerField):
    """Custom field using django IntegerField validation and rendering a gds text-input."""

    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                type="number",
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKPasswordInputField(GDSFieldMixin, forms.CharField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.PasswordInputKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKRadioInputField(GDSFieldMixin, forms.ChoiceField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            items = []
            for i, (value, label) in enumerate(self.field.choices):
                item = {"id": f"{self.auto_id}_{i}", "value": value, "text": label}
                if value in self.form.gds_radio_conditional_fields:
                    item["conditional"] = {"html": self.form.gds_radio_conditional_fields[value]}

                items.append(serializers.RadioItem(**item))

            serializer = serializers.RadioInputKwargs(
                name=self.name,
                fieldset=serializers.Fieldset(
                    legend=serializers.FieldsetLegend(
                        text=self.label, isPageHeading=True, classes="govuk-fieldset__legend--l"
                    )
                ),
                hint=self._get_hint(),
                items=items,
                value=self.value(),
                errorMessage=self._get_errors(),
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKSelectField(GDSFieldMixin, forms.ChoiceField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.SelectFieldKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                items=[
                    serializers.SelectItem(value=value, text=label)
                    for value, label in self.field.choices
                ],
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKSlugField(GDSFieldMixin, forms.SlugField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKTextareaField(GDSFieldMixin, forms.CharField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextareaFieldKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                # TODO: ECIL-323 Remove `or ""` after ECIL-323 is fixed.
                value=self.value() or "",
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context


class GovUKTextInputField(GDSFieldMixin, forms.CharField):
    class BF(GDSBoundField):
        def get_context(self) -> dict[str, Any]:
            context = super().get_context()

            serializer = serializers.TextInputKwargs(
                id=self.auto_id,
                name=self.name,
                label=self._get_label(),
                hint=self._get_hint(),
                value=self.value(),
                errorMessage=self._get_errors(),
                attributes=self.field.widget.attrs,
                **self.field.get_overrides(),
            )

            context["gds_kwargs"] = serializer.model_dump(exclude_defaults=True)

            return context
