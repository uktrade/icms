from unittest import mock

from django.shortcuts import reverse
from django.test import override_settings


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
