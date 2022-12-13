import enum

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models


class AddressEntryType(models.TextChoices):
    MANUAL = ("M", "Manual")
    SEARCH = ("S", "Search")


class YesNoChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")


class YesNoNAChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")
    not_applicable = ("n/a", "N/A")


class FirearmCommodity(models.TextChoices):
    EX_CHAPTER_93 = ("ex Chapter 93", "ex Chapter 93")
    EX_CHAPTER_97 = ("ex Chapter 97", "ex Chapter 97")


at_least_0 = MinValueValidator(limit_value=0.0)


class EnumJsonEncoder(DjangoJSONEncoder):
    """Extends DjangoJSONEncoder to support encoding Enum types."""

    def default(self, o):
        # This only works when o.value is JSON serializable (e.g. str and int)
        if isinstance(o, enum.Enum):
            return o.value
        else:
            return super().default(o)
