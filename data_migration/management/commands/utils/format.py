from typing import Any, Optional

from django.utils import timezone


def format_row(
    columns: list[str],
    row: list[Any],
    includes: Optional[list[str]] = None,
    pk: Optional[int] = None,
) -> dict[str, Any]:
    """Applies formatting to a row of sql data to be able to import into Django models

    :param columns: The columns returned from the query
    :param row: The row of data being formatted
    :param includes: The fields to be used when creating the model instance
    :param pk: The pk to set when creating the model instance
    """
    data = {}

    for column, value in zip(columns, row):
        if includes and column not in includes:
            continue

        if value and column.endswith("_datetime"):
            # TODO: Check timezone how timezones work in django.
            # Assumption that source is UTC and datetime is passed to models with source tz
            value = timezone.utc.localize(value)

        data[column] = value

    if pk:
        data["id"] = pk

    return data


def format_name(name: str) -> str:
    """Form a human readable named from underscored string

    "foo_bar" -> "Foo Bar"

    :param name: A string separated by underscores
    """
    return " ".join(w.capitalize() for w in name.split("_"))
