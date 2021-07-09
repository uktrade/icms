import pytest

from web.utils.currency import convert_gbp_to_euro


@pytest.mark.parametrize(
    "gbp,expected_euros",
    [
        (12345, 13703),
        (23456, 26036),
        (34567, 38369),
    ],
)
def test_convert_gbp_to_euro(gbp, expected_euros):
    actual_euros = convert_gbp_to_euro(gbp)

    assert actual_euros == expected_euros
