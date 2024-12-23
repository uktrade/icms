import pytest

from web.domains.country.utils import comma_separator


@pytest.mark.parametrize(
    "data,expected",
    [
        (["a"], "a"),
        (["a", "b"], "a and b"),
        (["a", "b", "c"], "a, b and c"),
        ([], ""),
    ],
)
def test_comma_separator(data, expected):
    assert comma_separator(data) == expected
