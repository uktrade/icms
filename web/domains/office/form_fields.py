import unicodedata

from django import forms


class AddressLineFormField(forms.CharField):
    """Address line field"""

    def clean(self, value):
        """
        Normalize address_line string to replace any unwanted characters.
        These characters may cause an issue when sending to CHIEF.
        """
        value = super().clean(value)
        if value:
            # Normalize string to remove unwanted characters
            value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("utf8")

            # manually replace grave accent (U+0060) with apostrophe (U+0027) as CHIEF does not support it
            value = value.replace("\u0060", "\u0027")
        return value
