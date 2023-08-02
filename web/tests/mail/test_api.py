from unittest import mock
from uuid import UUID

import pytest
from notifications_python_client.errors import HTTPError

from web.mail import api

HTTP_404_NOT_FOUND_ERROR = {
    "errors": [{"error": "NoResultFound", "message": "No result found"}],
    "status_code": 404,
}


@pytest.mark.parametrize(
    "template_id,expected_result,mock_get_template_id_response",
    [
        (UUID("4adda435-af30-4f24-98a4-1f07e222369e"), False, HTTP_404_NOT_FOUND_ERROR),
        (
            UUID("646bea34-20ef-437c-b001-ea557f3ba1e6"),
            True,
            {"id": "646bea34-20ef-437c-b001-ea557f3ba1e6"},
        ),
        (UUID("646bea34-20ef-437c-b001-ea557f3ba1e6"), False, {}),
        (
            UUID("646bea34-20ef-437c-b001-ea557f3ba1e6"),
            False,
            {"id": "fb9a1023-3901-44e8-a7d3-a0e309e93951"},
        ),
    ],
)
def test_is_valid_template_by_id(template_id, expected_result, mock_get_template_id_response):
    with mock.patch("web.mail.api.get_template_by_id") as mock_get_template_id:
        mock_get_template_id.return_value = mock_get_template_id_response
        assert api.is_valid_template_id(template_id) == expected_result


@mock.patch("notifications_python_client.NotificationsAPIClient.get_template")
def test_get_template_by_id(mock_gov_notify_get_template):
    fake_response = {"id": "fb9a1023-3901-44e8-a7d3-a0e309e93951"}
    mock_gov_notify_get_template.return_value = fake_response
    assert api.get_template_by_id(UUID("fb9a1023-3901-44e8-a7d3-a0e309e93951")) == fake_response


@mock.patch("notifications_python_client.NotificationsAPIClient.get_template")
def test_get_template_by_id_error(mock_gov_notify_get_template):
    fake_response = mock.Mock(status_code=404, json=lambda: HTTP_404_NOT_FOUND_ERROR)
    fake_error = mock.Mock(response=fake_response)
    mock_gov_notify_get_template.side_effect = HTTPError.create(fake_error)
    assert (
        api.get_template_by_id(UUID("fb9a1023-3901-44e8-a7d3-a0e309e93951"))
        == HTTP_404_NOT_FOUND_ERROR
    )


@mock.patch("notifications_python_client.NotificationsAPIClient.send_email_notification")
def test_send_email_error(mock_gov_notify_send_email_notification):
    fake_response = mock.Mock(status_code=404, json=lambda: HTTP_404_NOT_FOUND_ERROR)
    fake_error = mock.Mock(response=fake_response)
    mock_gov_notify_send_email_notification.side_effect = HTTPError.create(fake_error)
    with pytest.raises(HTTPError):
        api.send_email(
            UUID("fb9a1023-3901-44e8-a7d3-a0e309e93951"), {}, "tester@example.com"  # /PS-IGNORE
        )
