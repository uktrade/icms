import re
from typing import Any

import phonenumber_field.formfields
from django import forms
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from .utils import clean_postcode
from .widgets import DateInput


class PhoneNumberField(phonenumber_field.formfields.PhoneNumberField):
    widget = PhoneNumberInternationalFallbackWidget
    max_length = 60
    help_text = "Customary input formats:\n\
    \n\
    - FOR United Kingdom:\n\
    FORMAT: STD NUMBER\n\
    U.Kingdom: 020 12345678\n\
    - FOR International:\n\
    FORMAT: +CC (NDD)STD NUMBER\n\
    Netherlands: +31 (0)20 12345678\n\
    Hungary: +36 (06)1 12345678\n\
    U.Kingdom: +44 (0)20 12345678\n\
    - FOR International without NDD:\n\
    FORMAT: +CC STD NUMBER<br>Norway: +47 123 4568900\n\
    Spain: +34 911 12345678\n\
    America: +1 123 4568900"


class UKPostcodeField(forms.RegexField):
    # https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom#Validation
    UK_POSTCODE_REGEX = r"^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$"

    def __init__(self, regex=UK_POSTCODE_REGEX, **kwargs):
        kwargs.setdefault("required", True)
        kwargs.setdefault("label", "Postcode")
        kwargs.setdefault("error_messages", {"invalid": "Please enter a valid postcode"})

        super().__init__(regex, **kwargs)

    def to_python(self, value: Any) -> str:
        postcode: str = super().to_python(value)

        if postcode not in self.empty_values:
            postcode = clean_postcode(postcode)

        return postcode


class WildcardField(forms.RegexField):
    def to_python(self, value: str) -> str:
        """Strip multiple wildcard characters in a row with a single wildcard character.

        :param value: Incoming form value.
        """

        val = super().to_python(value)
        stripped = re.sub("%+", "%", val)

        return stripped


# Always match the format here: web/static/web/js/fox/core-footer.js
# dateFormat: "dd'-'M'-'yy"
JQUERY_DATE_FORMAT = "%d-%b-%Y"


class JqueryDateField(forms.DateField):
    widget = DateInput(format=JQUERY_DATE_FORMAT)
    input_formats = [JQUERY_DATE_FORMAT]
