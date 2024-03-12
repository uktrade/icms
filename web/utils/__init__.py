import datetime as dt
import re
import time as tm
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def time_snippet(msg: str) -> Generator[None, None, None]:
    print(f"Timing this: {msg}")
    start = tm.perf_counter()

    yield

    end = tm.perf_counter()
    duration = end - start

    print(f"Time taken: {duration} seconds")


def strip_spaces(*fields: str | None) -> str:
    """Replaces all whitespace characters in fields with a single space

    e.g.
    strip_spaces("123\n\nSesame   St", "ABC   123") -> "123 Sesame St ABC 123"
    """
    return " ".join(re.sub(r"\s+", " ", f"{f.strip()}") for f in fields if f)


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
