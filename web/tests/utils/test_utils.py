import datetime as dt

import pytest
from django.utils import timezone

from web.utils import datetime_format, day_ordinal_date, strip_spaces


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("123\n\nTest", "123   345", "123 Test 123 345"),
        (" 123\nTest\n", "\nABC 345 ", "123 Test ABC 345"),
        (" 123\nTest\n", "", "123 Test"),
        (" 123\nTest\n", None, "123 Test"),
    ],
)
def test_strip_spaces(a, b, expected):
    assert strip_spaces(a, b) == expected


@pytest.mark.parametrize(
    "date,expected",
    [
        (dt.date(2023, 1, 1), "1st January 2023"),
        (dt.date(2023, 2, 2), "2nd February 2023"),
        (dt.date(2023, 3, 3), "3rd March 2023"),
        (dt.date(2023, 4, 4), "4th April 2023"),
        (dt.date(2023, 5, 5), "5th May 2023"),
        (dt.date(2023, 6, 10), "10th June 2023"),
        (dt.date(2023, 7, 11), "11th July 2023"),
        (dt.date(2023, 8, 12), "12th August 2023"),
        (dt.date(2023, 9, 13), "13th September 2023"),
        (dt.date(2023, 10, 14), "14th October 2023"),
        (dt.date(2023, 11, 21), "21st November 2023"),
        (dt.date(2023, 12, 22), "22nd December 2023"),
        (dt.date(2024, 1, 23), "23rd January 2024"),
        (dt.date(2024, 2, 24), "24th February 2024"),
        (dt.date(2024, 3, 30), "30th March 2024"),
        (dt.date(2024, 5, 31), "31st May 2024"),
    ],
)
def test_day_ordinal_date(date, expected):
    assert day_ordinal_date(date) == expected


@pytest.mark.parametrize(
    ["dt_val", "tz", "expected_output"],
    [
        (
            dt.datetime(2024, 1, 31, 8, 30, 59, tzinfo=dt.UTC),
            "Europe/London",
            "31-Jan-2024 08:30:59",
        ),
        (
            dt.datetime(2024, 4, 1, 8, 30, 59, tzinfo=dt.UTC),
            "Europe/London",
            "01-Apr-2024 09:30:59",
        ),
        (
            dt.datetime(2024, 4, 1, 8, 30, 59, tzinfo=dt.UTC),
            "America/Araguaina",
            "01-Apr-2024 05:30:59",
        ),
        (
            dt.datetime(2024, 4, 1, 1, 20, 30, tzinfo=dt.UTC),
            "America/Araguaina",
            "31-Mar-2024 22:20:30",
        ),
    ],
)
def test_datetime_format(dt_val, tz, expected_output):
    timezone.activate(tz)
    actual_output = datetime_format(dt_val)

    assert expected_output == actual_output

    # Clear this so that it doesn't break other tests in the same thread.
    timezone.deactivate()
