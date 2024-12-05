from web.ecil.gds import forms as gds_forms


class TestGDSFormErrorSummary:
    class Form(gds_forms.GDSForm):
        text_input_field = gds_forms.GovUKTextInputField(
            label="What is the name of the event?",
            help_text="Sample help text",
            min_length=10,
            max_length=15,
        )

        date_input_field = gds_forms.GovUKDateInputField(
            label="When was your passport issued?",
            help_text="For example, 27 3 2007",
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

        radio_input_field = gds_forms.GovUKRadioInputField(
            label="How would you prefer to be contacted?",
            help_text="Select one option",
            choices=[
                ("text", "Text message"),
                ("text_two", "Text message 2"),
                ("text_three", "Text message 3"),
            ],
        )

        text_input_field = gds_forms.GovUKTextInputField(
            label="What is the name of the event?",
            help_text="Sample help text",
            min_length=10,
            max_length=15,
        )

    def test_error_summary_kwargs(self):
        form = self.Form(data={})

        assert form.error_summary_kwargs == {
            "errorList": [
                # Error href is the id of the field
                {"href": "#id_text_input_field", "text": ["You must enter this item"]},
                # Error href is the id of the first date field
                {"href": "#id_date_input_field_0", "text": ["Enter the day, month and year"]},
                # Error href is the id of the first checkbox field
                {"href": "#id_checkbox_field_0", "text": ["You must enter this item"]},
                # Error href is the id of the first radio field
                {"href": "#id_radio_input_field_0", "text": ["You must enter this item"]},
            ],
            "titleText": "There is a problem",
        }
