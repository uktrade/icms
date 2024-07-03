from typing import Any
from unittest import mock

from django.test.client import Client, RequestFactory

from web.one_login.utils import TOKEN_SESSION_KEY, get_one_login_logout_url


@mock.patch.multiple("web.one_login.utils", OneLoginConfig=mock.DEFAULT, autospec=True)
def test_get_one_login_logout_url(client: Client, rf: RequestFactory, **mocks: Any) -> None:
    mocks["OneLoginConfig"].return_value.end_session_url = "https://fake-one.login.gov.uk/logout/"

    request = rf.request()
    request.session = client.session
    request.session[TOKEN_SESSION_KEY] = {"id_token": "FAKE-TOKEN"}
    request.session.save()

    # Test without post logout callback url
    assert get_one_login_logout_url(request) == "https://fake-one.login.gov.uk/logout/"

    # Test with post logout callback url
    expected = "https://fake-one.login.gov.uk/logout/?id_token_hint=FAKE-TOKEN&post_logout_redirect_uri=https%3A%2F%2Fmy-site-post-logout-redirect%2F"
    actual = get_one_login_logout_url(request, "https://my-site-post-logout-redirect/")

    assert expected == actual
