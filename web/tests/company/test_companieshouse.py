from unittest.mock import Mock, patch

import pytest

from web.errors import APIError
from web.utils.companieshouse import api_get_companies


@patch("web.utils.companieshouse.requests.get")
def test_api_raises_error(_):
    """Raise an error when status code is not 200."""
    with pytest.raises(APIError):
        api_get_companies(query_string="my_search_request")


@patch("web.utils.companieshouse.requests.get")
def test_api_ok(mock_get):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"some_matched": "companies"}
    mock_get.return_value = response

    assert {"some_matched": "companies"} == api_get_companies(query_string="my_search_request")
