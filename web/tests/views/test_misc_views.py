from unittest import mock

import pytest
from django.shortcuts import reverse
from django.test import override_settings

from web.errors import APIError


class TestPostcodeLookup:

    def test_postcode_lookup_error(self, importer_client):
        url = reverse("misc:postcode-lookup")
        response = importer_client.post(url, data={})
        assert response.status_code == 400
        assert response.json() == {"error_msg": "Missing required field postcode"}

    @mock.patch("requests.get")
    def test_postcode_lookup(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"addresses": {"a": []}}
        mock_get.return_value.status_code = 200
        url = reverse("misc:postcode-lookup")
        response = importer_client.post(url, data={"postcode": "HA9 0WS"})  # /PS-IGNORE
        assert response.status_code == 200
        assert response.json() == {"a": []}

    @mock.patch("requests.get")
    def test_postcode_lookup_api_error_500(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"Message": "Internal Server Error"}
        mock_get.return_value.status_code = 500
        url = reverse("misc:postcode-lookup")
        response = importer_client.post(url, data={"postcode": "HA9 0WS"})  # /PS-IGNORE
        assert response.status_code == 400
        assert response.json() == {"error_msg": "Unable to lookup postcode"}

    @override_settings(APP_ENV="dev")
    @mock.patch("requests.get")
    def test_postcode_lookup_api_error_404(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"Message": "Internal Server Error"}
        mock_get.return_value.status_code = 404
        url = reverse("misc:postcode-lookup")
        response = importer_client.post(url, data={"postcode": "HA9 0WS"})  # /PS-IGNORE

        assert response.status_code == 400
        assert response.json() == {
            "error_msg": "Unable to find addresses for this postcode",
            "dev_error_msg": "status_code: 404: error: Internal Server Error",
        }

    @mock.patch("requests.get")
    @override_settings(APP_ENV="dev")
    def test_postcode_lookup_exception(self, mock_get, importer_client):
        mock_get.side_effect = Exception("Custom Error")
        url = reverse("misc:postcode-lookup")
        response = importer_client.post(url, data={"postcode": "HA9 0WS"})  # /PS-IGNORE
        assert response.status_code == 400
        assert response.json() == {"error_msg": "Unable to lookup postcode"}


class TestCompanyLookup:

    def test_company_lookup_error(self, importer_client):
        url = reverse("misc:company-lookup")
        response = importer_client.post(url, data={})
        assert response.status_code == 400
        assert response.json() == {"error_msg": "Missing required field query"}

    @mock.patch("requests.get")
    def test_company_lookup_error_404(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"companies": {"a": []}}
        mock_get.return_value.status_code = 404
        url = reverse("misc:company-lookup")
        with pytest.raises(APIError) as e:
            importer_client.post(url, data={"query": "Business 1"})  # /PS-IGNORE
        assert e.value.error_msg == "Unable to lookup company"

    @mock.patch("requests.get")
    def test_company_lookup(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"companies": {"a": []}}
        mock_get.return_value.status_code = 200
        url = reverse("misc:company-lookup")
        response = importer_client.post(url, data={"query": "Business 1"})  # /PS-IGNORE
        assert response.status_code == 200
        assert response.json() == {"companies": {"a": []}}
        assert (
            mock_get.call_args[0][0].endswith("search/companies?q=Business+1&items_per_page=20")
            is True
        )
        assert "Authorization" in mock_get.call_args.kwargs["headers"]


class TestCompanyNumberLookup:

    def test_company_number_lookup_error(self, importer_client):
        url = reverse("misc:company-number-lookup")
        response = importer_client.post(url, data={})
        assert response.status_code == 400
        assert response.json() == {"error_msg": "No company_number provided in POST request"}

    @override_settings(APP_ENV="dev")
    @mock.patch("requests.get")
    def test_company_number_lookup_error_404(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"company_number": "1234"}
        mock_get.return_value.status_code = 404
        url = reverse("misc:company-number-lookup")
        response = importer_client.post(url, data={"company_number": "1234"})  # /PS-IGNORE
        assert response.status_code == 404
        assert response.json() == {"error_msg": "Company not found"}

    @mock.patch("requests.get")
    def test_company_number_lookup_error_500(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"company_number": "1234"}
        mock_get.return_value.status_code = 500
        url = reverse("misc:company-number-lookup")
        response = importer_client.post(url, data={"company_number": "1234"})  # /PS-IGNORE
        assert response.status_code == 500
        assert response.json() == {"error_msg": "Unable to lookup company"}

    @mock.patch("requests.get")
    def test_company_number_lookup_unknown_error(self, mock_get, importer_client):
        mock_get.side_effect = Exception("Custom Error")
        url = reverse("misc:company-number-lookup")
        response = importer_client.post(url, data={"company_number": "1234"})  # /PS-IGNORE
        assert response.status_code == 500
        assert response.json() == {"error_msg": "Unable to lookup company"}

    @mock.patch("requests.get")
    def test_company_number_lookup(self, mock_get, importer_client):
        mock_get.return_value.json.return_value = {"company": "My Company"}
        mock_get.return_value.status_code = 200
        url = reverse("misc:company-number-lookup")
        response = importer_client.post(url, data={"company_number": "1234"})  # /PS-IGNORE
        assert response.status_code == 200
        assert response.json() == {"company": "My Company"}
        assert mock_get.call_args[0][0].endswith("company/1234") is True
        assert "Authorization" in mock_get.call_args.kwargs["headers"]
