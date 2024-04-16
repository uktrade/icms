from typing import Any

from django.utils import timezone

from data_migration.utils.format import (
    adjust_icms_v1_datetime,
    date_or_none,
    datetime_or_none,
)


def format_row(
    columns: list[str],
    row: list[Any],
    includes: list[str] | None = None,
    pk: int | None = None,
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

        if value and (
            column.endswith("_datetime") or column in ("created", "created_at", "updated_at")
        ):
            if isinstance(value, str):
                value = datetime_or_none(value)

            if timezone.is_naive(value):
                value = adjust_icms_v1_datetime(value)

        elif value and column.endswith("_date"):
            value = date_or_none(value)

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
