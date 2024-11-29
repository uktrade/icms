import datetime as dt
from decimal import Decimal
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from pytest_django.asserts import assertHTMLEqual

from web.ecil.gds import forms as gds


class TestGovUKCharacterCountField:
    class MaxLengthForm(gds.GDSForm):
        field = gds.GovUKCharacterCountField(
            label="Test label", help_text="Test help_text", max_length=5
        )

    class MaxWordsForm(gds.GDSForm):
        field = gds.GovUKCharacterCountField(
            label="Test label", help_text="Test help_text", max_words=5
        )

    def test_max_length_form_valid(self):
        data = {"field": "value"}
        form = self.MaxLengthForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "value"

    def test_max_length_form_invalid(self):
        data = {"field": "valuee"}
        form = self.MaxLengthForm(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value has at most 5 characters (it has 6)."]

    def test_max_length_template(self):
        data = {"field": "value"}
        form = self.MaxLengthForm(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group govuk-character-count" data-module="govuk-character-count" data-maxlength="5">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">Test label</label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">Test help_text</div>
                <textarea
                    class="govuk-textarea govuk-js-character-count" id="id_field" name="field" rows="5"
                    aria-describedby="id_field-info id_field-hint"
                    maxlength="5"
                >
                    value
                </textarea>
                <div id="id_field-info" class="govuk-hint govuk-character-count__message">
                  You can enter up to 5 characters
                </div>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)

    def test_max_words_form_valid(self):
        data = {"field": "this is a valid value"}
        form = self.MaxWordsForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "this is a valid value"

    def test_max_words_form_invalid(self):
        data = {"field": "this is not a valid value"}
        form = self.MaxWordsForm(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value has at most 5 words (it has 6)."]

    def test_max_words_template(self):
        data = {"field": "value"}
        form = self.MaxWordsForm(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group govuk-character-count"
                   data-module="govuk-character-count" data-maxwords="5">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <textarea class="govuk-textarea govuk-js-character-count" id="id_field" name="field" rows="5" aria-describedby="id_field-info id_field-hint">
                  value
                </textarea>
                <div id="id_field-info" class="govuk-hint govuk-character-count__message">
                  You can enter up to 5 words
                </div>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)

    def test_no_max_attributes_set_form(self):
        with pytest.raises(
            ValueError, match="You must specify either a max_length or max_words value."
        ):

            class NoMaxAttributeForm(gds.GDSForm):
                field = gds.GovUKCharacterCountField(label="Test label", help_text="Test help_text")

    def test_both_max_attributes_set_form(self):
        with pytest.raises(
            ValueError, match="You must only specify either a max_length or max_words value."
        ):

            class NoMaxAttributeForm(gds.GDSForm):
                field = gds.GovUKCharacterCountField(
                    label="Test label",
                    help_text="Test help_text",
                    max_length=1,
                    max_words=1,
                )


class TestGovUKCheckboxesField:
    class Form(gds.GDSForm):
        field = gds.GovUKCheckboxesField(
            label="Test label",
            help_text="Test help_text",
            choices=[("one", "One"), ("two", "Two"), ("three", "Three")],
        )

    def test_max_length_form_valid(self):
        data = {"field": ["one", "three"]}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data == {"field": ["one", "three"]}

    def test_form_invalid(self):
        data = {"field": ["four"]}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Select a valid choice. four is not one of the available choices."
        ]

    def test_template(self):
        data = {"field": ["one"]}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <fieldset class="govuk-fieldset" aria-describedby="field-hint">
                  <legend class="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 class="govuk-fieldset__heading">
                      Test label
                    </h1>
                  </legend>
                  <div id="field-hint" class="govuk-hint">
                    Test help_text
                  </div>
                  <div class="govuk-checkboxes" data-module="govuk-checkboxes">
                    <div class="govuk-checkboxes__item">
                      <input class="govuk-checkboxes__input" id="field" name="field" type="checkbox" value="one" checked>
                      <label class="govuk-label govuk-checkboxes__label" for="field">
                        One
                      </label>
                    </div>
                    <div class="govuk-checkboxes__item">
                      <input class="govuk-checkboxes__input" id="field-2" name="field" type="checkbox" value="two">
                      <label class="govuk-label govuk-checkboxes__label" for="field-2">
                        Two
                      </label>
                    </div>
                    <div class="govuk-checkboxes__item">
                      <input class="govuk-checkboxes__input" id="field-3" name="field" type="checkbox" value="three">
                      <label class="govuk-label govuk-checkboxes__label" for="field-3">
                        Three
                      </label>
                    </div>
                  </div>
                </fieldset>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKDateInputField:
    class Form(gds.GDSForm):
        field = gds.GovUKDateInputField(
            label="Test label",
            help_text="Test help_text",
        )

    def test_form_valid(self):
        data = {
            "field_0": "23",  # Day
            "field_1": "7",  # Month
            "field_2": "2022",  # Year
        }
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == dt.date(2022, 7, 23)

    def test_form_invalid(self):
        data = {
            "field_0": "23",  # Day
            "field_1": "13",  # Month
            "field_2": "2022",  # Year
        }
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["month must be in 1..12"]

        data = {
            "field_0": "23",  # Day
            "field_1": "12",  # Month
            "field_2": "-1",  # Year
        }
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Enter a valid year"]

        data = {
            "field_0": "45",  # Day
            "field_1": "12",  # Month
            "field_2": "2022",  # Year
        }
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["day is out of range for month"]

        data = {
            "field_0": "foo",  # Day
            "field_1": "bar",  # Month
            "field_2": "baz",  # Year
        }
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Enter a valid day",
            "Enter a valid month",
            "Enter a valid year",
        ]

    def test_template(self):
        data = {
            "field_0": "23",  # Day
            "field_1": "7",  # Month
            "field_2": "2022",  # Year
        }
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <fieldset class="govuk-fieldset" role="group" aria-describedby="id_field-hint">
                  <legend class="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 class="govuk-fieldset__heading">
                      Test label
                    </h1>
                  </legend>
                  <div id="id_field-hint" class="govuk-hint">
                    Test help_text
                  </div>
                  <div class="govuk-date-input"
                       id="id_field">
                    <div class="govuk-date-input__item">
                      <div class="govuk-form-group">
                        <label class="govuk-label govuk-date-input__label" for="id_field-field_0">
                          Day
                        </label>
                        <input class="govuk-input govuk-date-input__input " id="id_field-field_0" name="field_0" type="text" value="23" inputmode="numeric">
                      </div>
                    </div>
                    <div class="govuk-date-input__item">
                      <div class="govuk-form-group">
                        <label class="govuk-label govuk-date-input__label" for="id_field-field_1">
                          Month
                        </label>
                        <input class="govuk-input govuk-date-input__input " id="id_field-field_1" name="field_1" type="text" value="7" inputmode="numeric">
                      </div>
                    </div>
                    <div class="govuk-date-input__item">
                      <div class="govuk-form-group">
                        <label class="govuk-label govuk-date-input__label" for="id_field-field_2">
                          Year
                        </label>
                        <input class="govuk-input govuk-date-input__input " id="id_field-field_2" name="field_2" type="text" value="2022" inputmode="numeric">
                      </div>
                    </div>
                  </div>
                </fieldset>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKDecimalField:
    class Form(gds.GDSForm):
        field = gds.GovUKDecimalField(
            label="Test label",
            help_text="Test help_text",
            min_value=0,
            max_value=1000,
            max_digits=5,
            decimal_places=2,
        )

    def test_form_valid(self):
        data = {"field": "123.45"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == Decimal("123.45")

    def test_form_invalid(self):
        data = {"field": "123.456"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure that there are no more than 5 digits in total."]

    def test_template(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group govuk-form-group--error">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <p id="id_field-error" class="govuk-error-message">
                  <span class="govuk-visually-hidden">Error:</span> Enter a number.
                </p>
                <input
                  class="govuk-input govuk-input--error" id="id_field" name="field" type="number"
                  value="value" aria-describedby="id_field-hint id_field-error"
                  min="0" max="1000" step="0.01"
                >
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKEmailField:
    valid_email = "email@example.com"  # /PS-IGNORE

    class Form(gds.GDSForm):
        field = gds.GovUKEmailField(
            label="Test label",
            help_text="Test help_text",
        )

    def test_form_valid(self):
        data = {"field": self.valid_email}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == self.valid_email

    def test_form_invalid(self):
        data = {"field": "valuee"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Enter a valid email address."]

    def test_template(self):
        data = {"field": self.valid_email}
        form = self.Form(data=data)

        expected_html = f"""
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input
                  class="govuk-input" id="id_field" name="field" type="email" value="{self.valid_email}"
                  aria-describedby="id_field-hint"
                  maxlength="320"
                >
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKFileUploadField:
    class Form(gds.GDSForm):
        field = gds.GovUKFileUploadField(
            label="Test label",
            help_text="Test help_text",
        )

    def test_form_valid(self):
        f = SimpleUploadedFile("example.png", b"file_content")
        file_data = {"field": f}
        form = self.Form(data={}, files=file_data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == f

    @mock.patch("web.domains.file.utils.delete_file_from_s3")
    @mock.patch("web.domains.file.utils.validate_virus_check_result")
    def test_form_invalid(self, *mocks):
        f = SimpleUploadedFile("example.zip", b"file_content")
        file_data = {"field": f}
        form = self.Form(data={}, files=file_data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Invalid file extension. Only these extensions are allowed: bmp, csv, doc, docx, dotx,"
            " eml, gif, heic, jfif, jpeg, jpg, msg, odt, pdf, png, rtf, tif, tiff, txt, xls, xlsb,"
            " xlsx, xps"
        ]

    def test_template(self):
        f = SimpleUploadedFile("example.png", b"file_content")
        file_data = {"field": f}
        form = self.Form(data={}, files=file_data)

        email = "enquiries.ilb@icms.trade.dev.uktrade.io"  # /PS-IGNORE

        expected_html = f"""
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                  <br>
                  Contact <a href="mailto:{email}">{email}</a>
                  if you have any issues uploading files.
                </div>
                <input class="govuk-file-upload" id="id_field" name="field" type="file" aria-describedby="id_field-hint">
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKFloatField:
    class Form(gds.GDSForm):
        field = gds.GovUKFloatField(
            label="Test label",
            help_text="Test help_text",
            min_value=0,
            max_value=1000,
        )

    def test_form_valid(self):
        data = {"field": "123.45"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == 123.45

    def test_form_invalid(self):
        data = {"field": "1000.01"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value is less than or equal to 1000."]

    def test_template(self):
        data = {"field": "123.45"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input
                  class="govuk-input" id="id_field" name="field" type="number" value="123.45"
                  aria-describedby="id_field-hint"
                  min="0" max="1000" step="any"
                >
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKIntegerField:
    class Form(gds.GDSForm):
        field = gds.GovUKIntegerField(
            label="Test label",
            help_text="Test help_text",
            min_value=0,
            max_value=1000,
        )

    def test_form_valid(self):
        data = {"field": "123"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == 123

    def test_form_invalid(self):
        data = {"field": "1001"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value is less than or equal to 1000."]

        data = {"field": "1001.01"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Enter a whole number."]

    def test_template(self):
        data = {"field": "123"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input
                  class="govuk-input" id="id_field" name="field" type="number" value="123"
                  aria-describedby="id_field-hint"
                  min="0" max="1000"
                >
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKPasswordInputField:
    class Form(gds.GDSForm):
        field = gds.GovUKPasswordInputField(
            label="Test label",
            help_text="Test help_text",
        )

    def test_form_valid(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "value"

    def test_form_invalid(self):
        data = {"field": ""}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["You must enter this item"]

    def test_template(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group govuk-password-input" data-module="govuk-password-input">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <div class="govuk-input__wrapper govuk-password-input__wrapper">
                  <input
                    class="govuk-input govuk-password-input__input govuk-js-password-input-input" id="id_field" name="field" type="password"
                    spellcheck="false" value="value" aria-describedby="id_field-hint" autocomplete="current-password" autocapitalize="none">
                  <button
                    type="button" class="govuk-button govuk-button--secondary govuk-password-input__toggle govuk-js-password-input-toggle"
                    data-module="govuk-button" aria-controls="id_field" aria-label="Show password" hidden>
                    Show
                  </button>
                </div>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKRadioInputField:
    class Form(gds.GDSForm):
        field = gds.GovUKRadioInputField(
            label="Test label",
            help_text="Test help_text",
            choices=[("one", "One"), ("two", "Two"), ("three", "Three")],
        )

    class ConditionalForm(gds.GDSForm):
        one = gds.GovUKTextInputField(
            label="Conditional test label 1",
            help_text="Conditional help text 1",
            radio_conditional=True,
        )
        two = gds.GovUKTextInputField(
            label="Conditional test label 2",
            help_text="Conditional help text 2",
            radio_conditional=True,
        )
        three = gds.GovUKTextInputField(
            label="Conditional test label 3",
            help_text="Conditional help text 3",
            radio_conditional=True,
        )

        field = gds.GovUKRadioInputField(
            label="Test label",
            help_text="Test help_text",
            choices=[("one", "One"), ("two", "Two"), ("three", "Three")],
        )

        def clean(self):
            self.clean_radio_conditional_fields("field", ["one", "two", "three"])

    def test_form_valid(self):
        data = {"field": "two"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "two"

    def test_form_invalid(self):
        data = {"field": "four"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Select a valid choice. four is not one of the available choices."
        ]

    def test_template(self):
        data = {"field": "one"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <fieldset class="govuk-fieldset" aria-describedby="field-hint">
                  <legend class="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 class="govuk-fieldset__heading">
                      Test label
                    </h1>
                  </legend>
                  <div id="field-hint" class="govuk-hint">
                    Test help_text
                  </div>
                  <div class="govuk-radios" data-module="govuk-radios">
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field" name="field" type="radio" value="one"
                             checked>
                      <label class="govuk-label govuk-radios__label" for="field">
                        One
                      </label>
                    </div>
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field-2" name="field" type="radio" value="two">
                      <label class="govuk-label govuk-radios__label" for="field-2">
                        Two
                      </label>
                    </div>
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field-3" name="field" type="radio" value="three">
                      <label class="govuk-label govuk-radios__label" for="field-3">
                        Three
                      </label>
                    </div>
                  </div>
                </fieldset>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)

    def test_conditional_form_valid(self):
        data = {"field": "two", "two": "value"}
        form = self.ConditionalForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "two"

    def test_conditional_form_invalid(self):
        data = {"field": "two", "two": ""}
        form = self.ConditionalForm(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["two"] == ["You must enter this item"]

    def test_conditional_template(self):
        data = {"field": "two", "two": "value"}
        form = self.ConditionalForm(data=data)

        # The three conditional fields render as empty divs initially due to the div renderer.
        expected_html = """
            <div></div>
            <div></div>
            <div></div>
            <div>
              <div class="govuk-form-group">
                <fieldset class="govuk-fieldset" aria-describedby="field-hint">
                  <legend class="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <h1 class="govuk-fieldset__heading">
                      Test label
                    </h1>
                  </legend>
                  <div id="field-hint" class="govuk-hint">
                    Test help_text
                  </div>
                  <div class="govuk-radios" data-module="govuk-radios">
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field" name="field" type="radio" value="one" data-aria-controls="conditional-field">
                      <label class="govuk-label govuk-radios__label" for="field">
                        One
                      </label>
                    </div>
                    <div class="govuk-radios__conditional govuk-radios__conditional--hidden" id="conditional-field">
                      <div class="govuk-form-group">
                        <h1 class="govuk-label-wrapper">
                          <label class="govuk-label govuk-label--l" for="id_one">
                            Conditional test label 1
                          </label>
                        </h1>
                        <div id="id_one-hint" class="govuk-hint">
                          Conditional help text 1
                        </div>
                        <input class="govuk-input" id="id_one" name="one" type="text" aria-describedby="id_one-hint">
                      </div>
                    </div>
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field-2" name="field" type="radio" value="two" checked data-aria-controls="conditional-field-2">
                      <label class="govuk-label govuk-radios__label" for="field-2">
                        Two
                      </label>
                    </div>
                    <div class="govuk-radios__conditional" id="conditional-field-2">
                      <div class="govuk-form-group">
                        <h1 class="govuk-label-wrapper">
                          <label class="govuk-label govuk-label--l" for="id_two">
                            Conditional test label 2
                          </label>
                        </h1>
                        <div id="id_two-hint" class="govuk-hint">
                          Conditional help text 2
                        </div>
                        <input class="govuk-input" id="id_two" name="two" type="text" value="value" aria-describedby="id_two-hint">
                      </div>
                    </div>
                    <div class="govuk-radios__item">
                      <input class="govuk-radios__input" id="field-3" name="field" type="radio" value="three" data-aria-controls="conditional-field-3">
                      <label class="govuk-label govuk-radios__label" for="field-3">
                        Three
                      </label>
                    </div>
                    <div class="govuk-radios__conditional govuk-radios__conditional--hidden" id="conditional-field-3">
                      <div class="govuk-form-group">
                        <h1 class="govuk-label-wrapper">
                          <label class="govuk-label govuk-label--l" for="id_three">
                            Conditional test label 3
                          </label>
                        </h1>
                        <div id="id_three-hint" class="govuk-hint">
                          Conditional help text 3
                        </div>
                        <input class="govuk-input" id="id_three" name="three" type="text" aria-describedby="id_three-hint">
                      </div>
                    </div>
                  </div>
                </fieldset>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKSelectField:
    class Form(gds.GDSForm):
        field = gds.GovUKSelectField(
            label="Test label",
            help_text="Test help_text",
            choices=[("one", "One"), ("two", "Two"), ("three", "Three")],
        )

    def test_form_valid(self):
        data = {"field": "one"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "one"

    def test_form_invalid(self):
        data = {"field": "four"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Select a valid choice. four is not one of the available choices."
        ]

    def test_template(self):
        data = {"field": "one"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <select class="govuk-select" id="id_field" name="field" aria-describedby="id_field-hint">
                  <option value="one" selected>One</option>
                  <option value="two">Two</option>
                  <option value="three">Three</option>
                </select>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKSlugField:
    class Form(gds.GDSForm):
        field = gds.GovUKSlugField(
            label="Test label",
            help_text="Test help_text",
            max_length=5,
            allow_unicode=False,
        )

    class UnicodeForm(gds.GDSForm):
        field = gds.GovUKSlugField(
            label="Test label",
            help_text="Test help_text",
            max_length=5,
            allow_unicode=True,
        )

    def test_form_valid(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "value"

    def test_form_invalid(self):
        data = {"field": "☃☃☃☃☃"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens."
        ]

    def test_template(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input
                  class="govuk-input" id="id_field" name="field" type="text" value="value"
                  aria-describedby="id_field-hint"
                  maxlength="5"
                >
              </div>
            </div>

        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)

    def test_unicode_form_valid(self):
        data = {"field": "valüe"}
        form = self.UnicodeForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "valüe"

    def test_unicode_form_invalid(self):
        # A snowman isn't a Unicode letter
        data = {"field": "val☃e"}
        form = self.UnicodeForm(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == [
            "Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens."
        ]

    def test_unicode_template(self):
        data = {"field": "value"}
        form = self.UnicodeForm(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input
                  class="govuk-input" id="id_field" name="field" type="text" value="value"
                  aria-describedby="id_field-hint"
                  maxlength="5"
                >
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKTextareaField:
    class Form(gds.GDSForm):
        field = gds.GovUKTextareaField(label="Test label", help_text="Test help_text", max_length=5)

    def test_form_valid(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "value"

    def test_form_invalid(self):
        data = {"field": "valuee"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value has at most 5 characters (it has 6)."]

    def test_template(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <textarea class="govuk-textarea" id="id_field" name="field" rows="5" aria-describedby="id_field-hint" maxlength="5">
                  value
                </textarea>
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)


class TestGovUKTextInputField:
    class Form(gds.GDSForm):
        field = gds.GovUKTextInputField(
            label="Test label",
            help_text="Test help_text",
            max_length=5,
        )

    def test_form_valid(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        assert form.is_valid()
        assert form.cleaned_data["field"] == "value"

    def test_form_invalid(self):
        data = {"field": "valuee"}
        form = self.Form(data=data)

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert form.errors["field"] == ["Ensure this value has at most 5 characters (it has 6)."]

    def test_template(self):
        data = {"field": "value"}
        form = self.Form(data=data)

        expected_html = """
            <div>
              <div class="govuk-form-group">
                <h1 class="govuk-label-wrapper">
                  <label class="govuk-label govuk-label--l" for="id_field">
                    Test label
                  </label>
                </h1>
                <div id="id_field-hint" class="govuk-hint">
                  Test help_text
                </div>
                <input class="govuk-input" id="id_field" name="field" type="text" value="value" aria-describedby="id_field-hint" maxlength="5">
              </div>
            </div>
        """
        actual_html = form.as_div()

        assertHTMLEqual(expected_html, actual_html)
