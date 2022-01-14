from django.urls import reverse

from web.domains.chief.client import make_hawk_sender

JSON_TYPE = "application/json"
# This has to match the request, because it is used to calculate the request's
# Hawk MAC digest. Django's test client uses "testserver" by default.
SERVER_NAME = "testserver"


def make_testing_hawk_sender(method: str, url: str, **kwargs):
    url = f"http://{SERVER_NAME}{url}"

    return make_hawk_sender(method, url, **kwargs)


class TestLicenseDataCallback:
    def test_auth_valid(self, client):
        url = reverse("chief:license-data-callback")
        content = b'{"foo": "bar"}'
        sender = make_testing_hawk_sender("PUT", url, content=content, content_type=JSON_TYPE)
        response = client.put(
            url, content, content_type=JSON_TYPE, HTTP_AUTHORIZATION=sender.request_header
        )

        assert response.status_code == 207

        server_auth = response.headers["Server-authorization"]
        # This will blow up if the signature does not match.
        sender.accept_response(
            server_auth, content=response.content, content_type=response.headers["Content-type"]
        )

    def test_auth_invalid(self, client):
        url = reverse("chief:license-data-callback")
        response = client.put(url, HTTP_AUTHORIZATION="Hawk foo")

        assert response.status_code == 400  # Bad request.
