from typing import Any

from django import forms
from django.db import models
from django.forms.utils import ErrorDict

from web.ecil.gds import component_serializers as serializers

from . import fields as gds_fields


class GDSFormMixin:
    # Used to display the gds error summary
    GDS_FORM = True

    # Extra type hints for clarity
    fields: dict[str, forms.Field]
    errors: ErrorDict | None
    cleaned_data: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # See this file to understand gds_radio_conditional_fields:
        #   - web/templates/ecil/gds/forms/field.html
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

        error_list = []

        for field_name, error in self.errors.items():
            match self.fields[field_name]:
                case gds_fields.GovUKDateInputField():
                    # Default the date input link to the first field.
                    href = f"#id_{field_name}_0"
                case gds_fields.GovUKCheckboxesField():
                    # Default to the first checkbox item
                    href = f"#id_{field_name}_0"
                case gds_fields.GovUKRadioInputField():
                    # Default to the first radio item
                    href = f"#id_{field_name}_0"
                case _:
                    href = f"#id_{field_name}"

            error_list.append(serializers.error_summary.Error(text=", ".join(error), href=href))

        return serializers.error_summary.ErrorSummaryKwargs(
            titleText="There is a problem", errorList=error_list
        ).model_dump(exclude_defaults=True)


class GDSForm(GDSFormMixin, forms.Form): ...  # noqa: E701


def get_gds_formfield(db_field: models.Field, **kwargs: Any) -> forms.Field:
    """Return an appropriate django form field foe each db_field type.

    Used this to determine form field type:
    https://docs.djangoproject.com/en/5.1/topics/forms/modelforms/#field-types
    """

    if not kwargs.get("label"):
        kwargs["label"] = db_field.verbose_name

    if not kwargs.get("help_text"):
        kwargs["help_text"] = db_field.help_text

    if db_field.blank:
        kwargs["required"] = False

    match db_field:
        #
        # CharField and child classes (child classes before parent class)
        case models.EmailField():
            field_cls = gds_fields.GovUKEmailField

        case models.SlugField():
            field_cls = gds_fields.GovUKSlugField

        case models.CharField():
            # Render the char field with choices as a radio group
            if db_field.choices:
                field_cls = gds_fields.GovUKRadioInputField
                kwargs["choices"] = db_field.choices
            else:
                if db_field.null:
                    kwargs["empty_value"] = None
                if db_field.max_length:
                    kwargs["max_length"] = db_field.max_length

                field_cls = gds_fields.GovUKTextInputField

        #
        # IntegerField and child classes (child classes before parent class)
        case models.PositiveBigIntegerField():
            field_cls = gds_fields.GovUKIntegerField
            kwargs |= {"min_value": 0, "max_value": models.PositiveBigIntegerField.MAX_BIGINT}

        case models.BigIntegerField():
            field_cls = gds_fields.GovUKIntegerField
            max_value = models.BigIntegerField.MAX_BIGINT
            kwargs |= {"min_value": -max_value - 1, "max_value": max_value}

        case models.PositiveSmallIntegerField():
            field_cls = gds_fields.GovUKIntegerField
            kwargs["min_value"] = 0

        case models.SmallIntegerField():
            # Default Django form field: IntegerField
            field_cls = gds_fields.GovUKIntegerField

        case models.PositiveIntegerField():
            field_cls = gds_fields.GovUKIntegerField
            kwargs["min_value"] = 0

        case models.IntegerField():
            field_cls = gds_fields.GovUKIntegerField

        #
        # All Other fields that inherit directly from Field
        case models.BinaryField():
            field_cls = gds_fields.GovUKTextInputField

        case models.BooleanField():
            if db_field.null:
                choices = [("True", "Yes"), ("False", "No"), ("", "N/a")]
                kwargs["required"] = False
            else:
                choices = [("True", "Yes"), ("False", "No")]

            kwargs["choices"] = choices
            field_cls = gds_fields.GovUKRadioInputField

        case models.DateTimeField():
            # Unsupported but need to define here as it's a subclass of DateField
            field_cls = db_field.formfield

        case models.DateField():
            # Default Django form field: DateField
            field_cls = gds_fields.GovUKDateInputField

        case models.DecimalField():
            df: models.DecimalField = db_field
            kwargs["max_digits"] = df.max_digits
            kwargs["decimal_places"] = df.decimal_places
            field_cls = gds_fields.GovUKDecimalField

        case models.FileField():
            field_cls = gds_fields.GovUKFileUploadField

        case models.FloatField():
            field_cls = gds_fields.GovUKFloatField

        case models.TextField():
            if db_field.max_length:
                kwargs["max_length"] = db_field.max_length
                field_cls = gds_fields.GovUKCharacterCountField
            else:
                field_cls = gds_fields.GovUKTextareaField

        # Fields not supported by either ModelForm or GDS components.
        case (
            models.AutoField()
            | models.BigAutoField()
            | models.DurationField()
            | models.FilePathField()
            | models.ForeignKey()
            | models.ImageField()
            | models.GenericIPAddressField()
            | models.JSONField()
            | models.ManyToManyField()
            | models.SmallAutoField()
            | models.TimeField()
            | models.URLField()
            | models.UUIDField()
        ):
            field_cls = db_field.formfield

        case _:
            raise ValueError(f"Unsupported db_field: {db_field}")

    return field_cls(**kwargs)


class GDSModelForm(GDSFormMixin, forms.ModelForm):
    class Meta:
        formfield_callback = get_gds_formfield


class GDSFormfieldCallback:
    def __init__(
        self,
        *,
        conditional_fields: list[str] | None = None,
        gds_field_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Callable class that sets conditional fields.

        :param conditional_fields: list of conditional fields that are used by GovUKRadioInputField.
        :param gds_field_kwargs: Overrides to pass to the gds template macro.
        """

        self.conditional_fields = conditional_fields or []
        self.gds_field_kwargs = gds_field_kwargs or {}

    def __call__(self, db_field: models.Field, **kwargs: Any) -> forms.Field:
        if db_field.name in self.conditional_fields:
            kwargs["radio_conditional"] = True

        if db_field.name in self.gds_field_kwargs.keys():
            kwargs["gds_field_kwargs"] = self.gds_field_kwargs[db_field.name]

        return get_gds_formfield(db_field, **kwargs)
