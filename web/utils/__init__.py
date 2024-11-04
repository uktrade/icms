import datetime as dt
import re
import time as tm
from collections.abc import Generator
from contextlib import contextmanager

from django.utils import timezone

from .sentry import capture_exception, capture_message


@contextmanager
def time_snippet(msg: str) -> Generator[None, None, None]:
    print(f"Timing this: {msg}")
    start = tm.perf_counter()

    yield

    end = tm.perf_counter()
    duration = end - start

    print(f"Time taken: {duration} seconds")


def clean_whitespace(field: str) -> str:
    """Replaces all whitespace characters in a field with a single space

    e.g.
    "123\n\nSesame   St\r\n" -> 123 Sesame St
    """
    return re.sub(r"\s+", " ", f"{field.strip()}")


def newlines_to_commas(field: str) -> str:
    """Normilizes address text fields to separate data with commas rather than newlines

    e.g.
    "123 Sesame St\nSesame Land\n\nSesame" -> "123 Sesame St, Sesame Land, Sesame"
    "123 Sesame St,\nSesame Land,\n\n Sesame" -> "123 Sesame St, Sesame Land, Sesame"
    """
    field = re.sub(r"(\s+)?(,)?(\s+)?(\n+)", ", ", field.strip())
    field = clean_whitespace(field.strip(","))
    return re.sub(r"(,)(( ,)+|(,)+)", ",", field)


def strip_spaces(*fields: str | None) -> str:
    """Replaces all whitespace characters in fields with a single space

    e.g.
    strip_spaces("123\n\nSesame   St", "ABC   123") -> "123 Sesame St ABC 123"
    """
    return " ".join(clean_whitespace(f) for f in fields if f)


def datetime_format(
    value: dt.datetime, _format: str = "%d-%b-%Y %H:%M:%S", local: bool = True
) -> str:
    """Format a datetime.datetime instance to the supplied format.

    Does the following:
      - Convert a timezone aware datetime in to the localtime.
      - Return the datetime formatted by the supplied format.

    The value is converted to the local timezone unless local is False.
    """

    if local:
        try:
            if isinstance(value, dt.datetime):
                value = timezone.localtime(value)
            else:
                capture_message(f"Tried to use datetime_format with: {value}")
        except ValueError:
            # Capture errors where a naive datetime is being used.
            # We should fix any naive datetime instances as ICMS defines USE_TZ = True
            capture_exception()

    return value.strftime(_format)


def day_ordinal_date(date: dt.date) -> str:
    """Get the date string with a day ordinal

    Returns string of date as "{day ordinal} {month name} {year}"
    e.g. 1st March 2023"""
    day = date.day

    match day:
        case 1 | 21 | 31:
            suffix = "st"
        case 2 | 22:
            suffix = "nd"
        case 3 | 23:
            suffix = "rd"
        case _:
            suffix = "th"

    return f"{day}{suffix} {date.strftime('%B %Y')}"


def is_northern_ireland_postcode(postcode: str | None) -> bool:
    """Returns true if the supplied postcode is an NI postcode."""

    if not postcode:
        return False

    return postcode.casefold().startswith("bt")
