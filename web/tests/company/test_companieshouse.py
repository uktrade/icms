from unittest.mock import Mock, patch

import pytest

from web.company.companieshouse import CompaniesHouseException, api_get_companies


@patch("web.company.companieshouse.requests.get")
def test_api_raises_error(_):
    """Raise an error when status code is not 200."""
    with pytest.raises(CompaniesHouseException):
        api_get_companies(query_string="my_search_request")


@patch("web.company.companieshouse.requests.get")
def test_api_ok(mock_get):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"some_matched": "companies"}
    mock_get.return_value = response

    assert {"some_matched": "companies"} == api_get_companies(query_string="my_search_request")
