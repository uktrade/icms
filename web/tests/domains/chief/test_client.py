from unittest import mock

from django.test import override_settings

from web.domains.chief import client


class TestChiefClient:
    def test_client_request(self, requests_mock):
        chief_url = "http://example.com/update"
        mock_response_headers = {
            "Content-Type": "text/plain",
            "Server-Authorization": 'Hawk mac="fake-mac", hash="fake-hash"',
        }
        requests_mock.post(chief_url, headers=mock_response_headers, text="OK")
        # Finished mocking the API response.

        data = {"foo": "bar"}

        with mock.patch("mohawk.sender.Sender.accept_response"):
            with override_settings(CHIEF_LICENSE_URL=chief_url):
                response = client.request_license(data)

        assert response.status_code == 200
        assert response.content == b"OK"
        assert response.headers["Content-type"] == "text/plain"
