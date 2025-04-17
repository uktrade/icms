from http import HTTPStatus
from typing import Any

from web.tests.api_auth import make_testing_hawk_sender


class BaseTestDataView:
    def test_authentication_failure(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_authentication_failure_hmrc_creds(self):
        sender = make_testing_hawk_sender(
            "GET", self.url, api_type="hmrc", content="", content_type=""
        )
        response = self.client.get(self.url, HTTP_AUTHORIZATION=sender.request_header)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_authetication(self):
        sender = make_testing_hawk_sender(
            "GET", self.url, api_type="data_workspace", content="", content_type=""
        )
        response = self.client.get(self.url, HTTP_AUTHORIZATION=sender.request_header)
        assert response.status_code == HTTPStatus.OK
        result = response.json()
        self.check_result(result)

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert True
