from django.db import models
from django.utils.text import capfirst

from .form_fields import AddressLineFormField


class AddressLineField(models.CharField):
    """Address line field for office addresses"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "required": not self.blank,
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "max_length": self.max_length,
        }
        defaults.update(kwargs)
        return AddressLineFormField(**defaults)
