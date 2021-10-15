import re

import phonenumber_field.formfields
from django import forms
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget


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


class WildcardField(forms.RegexField):
    def to_python(self, value: str) -> str:
        """Strip multiple wildcard characters in a row with a single wildcard character.

        :param value: Incoming form value.
        """

        val = super().to_python(value)
        stripped = re.sub("%+", "%", val)

        return stripped
