from typing import Any

from django import forms

from web.ecil.gds import forms as gds_forms


class GDSForm(gds_forms.GDSFormMixin, forms.Form):
    text_input_field = gds_forms.GovUKTextInputField(
        label="What is the name of the event?",
        help_text="Sample help text",
        min_length=10,
        max_length=15,
    )

    # Conditional field for "radio_input_field" field
    text = gds_forms.GovUKTextInputField(
        label="I am a conditional field",
        help_text="With some helptext",
        radio_conditional=True,
    )

    # Conditional field for "radio_input_field" field
    text_two = gds_forms.GovUKTextInputField(
        label="I am another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
    )

    # Conditional field for "radio_input_field" field
    text_three = gds_forms.GovUKTextInputField(
        label="I am yet another conditional field",
        help_text="With some helptext",
        radio_conditional=True,
    )

    radio_input_field = gds_forms.GovUKRadioInputField(
        label="How would you prefer to be contacted?",
        help_text="Select one option",
        choices=[
            ("text", "Text message"),
            ("text_two", "Text message 2"),
            ("text_three", "Text message 3"),
        ],
    )

    character_count_field = gds_forms.GovUKCharacterCountField(
        label="Can you provide more detail?",
        help_text=(
            "Do not include personal or financial information like your National Insurance number"
            " or credit card details"
        ),
        max_length=100,
    )

    checkbox_field = gds_forms.GovUKCheckboxesField(
        label="Which types of waste do you transport?",
        help_text="Select all that apply",
        choices=[
            ("carcasses", "Waste from animal carcasses"),
            ("mines", "Waste from mines or quarries"),
            ("farm", "Farm or agricultural waste"),
        ],
    )

    date_input_field = gds_forms.GovUKDateInputField(
        label="When was your passport issued?",
        help_text="For example, 27 3 2007",
    )

    file_upload_field = gds_forms.GovUKFileUploadField(
        label="Upload a file",
        help_text="Only pictures of dogs allowed",
    )

    password_field = gds_forms.GovUKPasswordInputField(
        label="Password", help_text="Is it secret? Is it safe?"
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
    )

    textarea_field = gds_forms.GovUKTextareaField(
        label="Can you provide more detail?",
        help_text=(
            "Do not include personal or financial information, like your National Insurance number"
            " or credit card details"
        ),
    )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        self.clean_radio_conditional_fields("radio_input_field", ["text", "text_two", "text_three"])

        return cleaned_data
