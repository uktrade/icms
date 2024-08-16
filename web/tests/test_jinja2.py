import datetime as dt

import pytest
from django.utils import timezone

from web.jinja2 import datetime_format


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
