from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import ngettext_lazy


@deconstructible
class MaxWordsValidator(BaseValidator):
    message = ngettext_lazy(
        "Ensure this value has at most %(limit_value)d words (it has " "%(show_value)d).",
        "Ensure this value has at most %(limit_value)d words (it has " "%(show_value)d).",
        "limit_value",
    )
    code = "max_words"

    def compare(self, a: int, b: int) -> bool:
        """Return True if the cleaned value exceeds the limit.

        :param a: cleaned value
        :param b: limit value
        """

        return a > b

    def clean(self, x: str) -> int:
        return len(x.split())
