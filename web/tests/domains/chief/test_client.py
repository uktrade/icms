from unittest import mock

from django.test import override_settings

from web.domains.chief import client


class TestChiefClient:
    def test_client_request(self, requests_mock):
        example_domain = "http://example.com/"
        chief_url = "update"
        url = f"{example_domain}{chief_url}"

        mock_response_headers = {
            "Content-Type": "text/plain",
            "Server-Authorization": 'Hawk mac="fake-mac", hash="fake-hash"',
        }
        requests_mock.post(url, headers=mock_response_headers, text="OK")
        # Finished mocking the API response.

        data = FakeData()
        with mock.patch("mohawk.sender.Sender.accept_response"):
            with override_settings(
                ICMS_HMRC_DOMAIN=example_domain, ICMS_HMRC_UPDATE_LICENCE_ENDPOINT=chief_url
            ):
                response = client.request_license(data)

        assert response.status_code == 200
        assert response.content == b"OK"
        assert response.headers["Content-type"] == "text/plain"


class FakeData:
    def json(self):
        return '{"foo": "bar"}'
