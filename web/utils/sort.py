import re

from django.db.models import Model, QuerySet


def extract_int_from_str(string: str) -> int:
    match = re.findall(r"^\d+", string)
    return int(match[0]) if match else 0


def sort_integer_strings(queryset: QuerySet, field: str) -> list[Model]:
    return sorted(
        queryset, key=lambda obj: (extract_int_from_str(getattr(obj, field)), getattr(obj, field))
    )
