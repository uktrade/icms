import enum

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator

from web.types import TypedTextChoices


class AddressEntryType(TypedTextChoices):
    MANUAL = ("MANUAL", "Manual")
    SEARCH = ("SEARCH", "Search")


class YesNoChoices(TypedTextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")


class YesNoNAChoices(TypedTextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")
    not_applicable = ("n/a", "N/A")


class FirearmCommodity(TypedTextChoices):
    EX_CHAPTER_93 = ("ex Chapter 93", "ex Chapter 93")
    EX_CHAPTER_97 = ("ex Chapter 97", "ex Chapter 97")


class ArchiveReasonChoices(TypedTextChoices):
    REVOKED = ("REVOKED", "Revoked")
    WITHDRAWN = ("WITHDRAWN", "Withdrawn")
    REFUSED = ("REFUSED", "Refused")
    OTHER = ("OTHER", "Other")


at_least_0 = MinValueValidator(limit_value=0.0)


class EnumJsonEncoder(DjangoJSONEncoder):
    """Extends DjangoJSONEncoder to support encoding Enum types."""

    def default(self, o):
        # This only works when o.value is JSON serializable (e.g. str and int)
        if isinstance(o, enum.Enum):
            return o.value
        else:
            return super().default(o)
