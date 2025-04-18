import datetime as dt
from typing import Any

from django.utils import timezone

from web.domains.commodity.models import Commodity
from web.ecil.gds import forms as gds_forms
from web.models import ECILExample, ECILMultiStepExample

# Example override config to pass to the GDS macros
LABEL_HEADER = {"label": {"isPageHeading": True, "classes": "govuk-label--l"}}
FIELDSET_LABEL_HEADER = {
    "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
}


class ExampleGDSForm(gds_forms.GDSForm):
    text_input_field = gds_forms.GovUKTextInputField(
        label="What is the name of the event?",
        help_text="Sample help text",
        min_length=10,
        max_length=15,
        gds_field_kwargs=LABEL_HEADER,
    )

    # Conditional field for "radio_input_field" field
    text = gds_forms.GovUKTextInputField(
        label="I am a conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    # Conditional field for "radio_input_field" field
    text_two = gds_forms.GovUKTextInputField(
        label="I am another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    # Conditional field for "radio_input_field" field
    text_three = gds_forms.GovUKTextInputField(
        label="I am yet another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    radio_input_field = gds_forms.GovUKRadioInputField(
        label="How would you prefer to be contacted?",
        help_text="Select one option",
        choices=[
            ("text", "Text message"),
            ("text_two", "Text message 2"),
            ("text_three", "Text message 3"),
        ],
        gds_field_kwargs=FIELDSET_LABEL_HEADER,
    )

    character_count_field = gds_forms.GovUKCharacterCountField(
        label="Can you provide more detail?",
        help_text=(
            "Do not include personal or financial information like your National Insurance number"
            " or credit card details"
        ),
        max_length=100,
        gds_field_kwargs=LABEL_HEADER,
    )

    checkbox_field = gds_forms.GovUKCheckboxesField(
        label="Which types of waste do you transport?",
        help_text="Select all that apply",
        choices=[
            ("carcasses", "Waste from animal carcasses"),
            ("mines", "Waste from mines or quarries"),
            ("farm", "Farm or agricultural waste"),
        ],
        gds_field_kwargs=FIELDSET_LABEL_HEADER,
    )

    date_input_field = gds_forms.GovUKDateInputField(
        label="When was your passport issued?",
        help_text="For example, 27 3 2007",
        gds_field_kwargs=FIELDSET_LABEL_HEADER,
    )

    file_upload_field = gds_forms.GovUKFileUploadField(
        label="Upload a file",
        help_text="Only pictures of dogs allowed",
        gds_field_kwargs=LABEL_HEADER,
    )

    password_field = gds_forms.GovUKPasswordInputField(
        label="Password",
        help_text="Is it secret? Is it safe?",
        gds_field_kwargs=LABEL_HEADER,
    )

    select_field = gds_forms.GovUKSelectField(
        label="Sort by",
        help_text="Select a value to sort items by",
        choices=[
            (None, "----"),
            ("published", "Recently published"),
            ("updated", "Recently updated"),
            ("views", "Most views"),
            ("comments", "Most comments"),
        ],
        gds_field_kwargs=LABEL_HEADER,
    )

    autocomplete_select = gds_forms.GovUKSelectField(
        label="What countries do you want to export to?",
        help_text="Start typing a country to add it.",
        choices=[
            (None, ""),
            ("1", "France"),
            ("2", "Germany"),
            ("3", "United Kingdom"),
        ],
        gds_field_kwargs=LABEL_HEADER,
    )

    textarea_field = gds_forms.GovUKTextareaField(
        label="Can you provide more detail?",
        help_text=(
            "Do not include personal or financial information, like your National Insurance number"
            " or credit card details"
        ),
        gds_field_kwargs=LABEL_HEADER,
    )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        self.clean_radio_conditional_fields("radio_input_field", ["text", "text_two", "text_three"])

        return cleaned_data


class ExampleGDSModelForm(gds_forms.GDSModelForm):
    foreign_key_field = gds_forms.GovUKSelectModelField(
        label="Foreign key field",
        help_text="Choose a commodity code from the list.",
        queryset=Commodity.objects.none(),
        error_messages={"required": "Select a commodity code"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["foreign_key_field"].queryset = Commodity.objects.filter(
            commodity_code__startswith="500500"
        )

        # hardcode unsupported fields so save works.
        self.instance.datetime_field = timezone.now()
        self.instance.duration_field = dt.timedelta(days=1, hours=2)
        self.instance.ip_address_field = "127.0.0.1"
        self.instance.json_field = {}
        self.instance.time_field = timezone.now().time()

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILExample
        fields = [
            # Supported GDS Fields
            "big_integer_field",
            # "editable_binary_field",
            "boolean_field",
            "optional_boolean_field",
            "char_field",
            "char_choice_field",
            "optional_char_field",
            "date_field",
            "decimal_field",
            "email_field",
            "float_field",
            "integer_field",
            "positive_big_integer_field",
            "positive_integer_field",
            "positive_small_integer_field",
            "slug_field",
            "small_integer_field",
            "text_field",
            # Currently unsupported (Defaulting to Django default field)
            # "datetime_field",
            # "duration_field",
            "foreign_key_field",
            # "ip_address_field",
            # "json_field",
            # "many_to_many_field",
            # "time_field",
            # "url_field",
            # "uuid_field",
        ]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "big_integer_field": LABEL_HEADER,
                "boolean_field": FIELDSET_LABEL_HEADER,
                "optional_boolean_field": FIELDSET_LABEL_HEADER,
                "char_field": LABEL_HEADER,
                "char_choice_field": FIELDSET_LABEL_HEADER,
                "optional_char_field": LABEL_HEADER,
                "date_field": FIELDSET_LABEL_HEADER,
                "decimal_field": LABEL_HEADER,
                "email_field": LABEL_HEADER,
                "float_field": LABEL_HEADER,
                "integer_field": LABEL_HEADER,
                "positive_big_integer_field": LABEL_HEADER,
                "positive_integer_field": LABEL_HEADER,
                "positive_small_integer_field": LABEL_HEADER,
                "slug_field": LABEL_HEADER,
                "small_integer_field": LABEL_HEADER,
                "text_field": LABEL_HEADER,
            }
        )


class ExampleConditionalGDSModelForm(gds_forms.GDSModelForm):
    # Conditional field for "char_choice_field" field
    blue = gds_forms.GovUKTextInputField(
        label="I am a conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    # Conditional field for "char_choice_field" field
    red = gds_forms.GovUKTextInputField(
        label="I am another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    # Conditional field for "char_choice_field" field
    yellow = gds_forms.GovUKTextInputField(
        label="I am yet another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
        gds_field_kwargs=LABEL_HEADER,
    )

    class Meta:
        model = ECILExample
        fields = ["blue", "red", "yellow", "char_choice_field"]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            conditional_fields=["blue", "red", "yellow"],
            gds_field_kwargs={"char_choice_field": FIELDSET_LABEL_HEADER},
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        self.clean_radio_conditional_fields("char_choice_field", ["blue", "red", "yellow"])

        return cleaned_data


class ExampleMultiStepStepOneForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILMultiStepExample
        fields = ["favourite_colour"]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"favourite_colour": FIELDSET_LABEL_HEADER}
        )


class ExampleMultiStepStepTwoForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILMultiStepExample
        fields = ["likes_cake"]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"likes_cake": FIELDSET_LABEL_HEADER}
        )


class ExampleMultiStepStepThreeForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILMultiStepExample
        fields = ["favourite_book"]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"favourite_book": LABEL_HEADER}
        )


# TODO: Revisit in ECIL-606
# gds_forms.GDSModelForm and ModelForm validate likes_cake differently
# Fix the BooleanField
# The summary form is just used for validation and therefore shouldn't need to be a GDSModelForm
class ExampleMultiStepStepSummaryForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILMultiStepExample
        fields = ["favourite_colour", "likes_cake", "favourite_book"]
