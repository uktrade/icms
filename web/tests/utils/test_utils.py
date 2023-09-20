import datetime as dt

import pytest

from web.utils import day_ordinal_date, strip_spaces


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
