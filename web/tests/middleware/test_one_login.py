from unittest import mock

from django.http import HttpResponseRedirect
from django.urls import reverse

from web.middleware.one_login import UserFullyRegisteredMiddleware
from web.one_login.constants import ONE_LOGIN_UNSET_NAME


class TestUserFullyRegisteredMiddleware:
    def test_middleware_redirects_to_edit_new_user_first_name(self, rf, importer_one_contact):
        request = rf.request()

        importer_one_contact.first_name = ONE_LOGIN_UNSET_NAME
        importer_one_contact.save()

        request.path = reverse("workbasket")
        request.user = importer_one_contact

        with mock.patch("web.middleware.one_login.messages") as mock_messages:
            middleware = UserFullyRegisteredMiddleware(mock.Mock())
            response: HttpResponseRedirect = middleware(request)

            assert mock_messages.info.call_count == 1
            assert mock_messages.info.call_args == mock.call(
                request, "Please set your first and last name."  # /PS-IGNORE
            )

        assert response.status_code == 302
        assert response.url == reverse("new-user-edit")

    def test_middleware_redirects_to_edit_new_user_last_name(self, rf, importer_one_contact):
        request = rf.request()

        importer_one_contact.last_name = ONE_LOGIN_UNSET_NAME
        importer_one_contact.save()

        request.path = reverse("workbasket")
        request.user = importer_one_contact

        with mock.patch("web.middleware.one_login.messages") as mock_messages:
            middleware = UserFullyRegisteredMiddleware(mock.Mock())
            response: HttpResponseRedirect = middleware(request)

            assert mock_messages.info.call_count == 1
            assert mock_messages.info.call_args == mock.call(
                request, "Please set your first and last name."  # /PS-IGNORE
            )

        assert response.status_code == 302
        assert response.url == reverse("new-user-edit")

    def test_middleware_does_not_redirect_to_edit_user(self, rf, importer_one_contact):
        request = rf.request()

        request.path = reverse("workbasket")
        request.user = importer_one_contact

        mock_get_response = mock.Mock()
        middleware = UserFullyRegisteredMiddleware(mock_get_response)
        middleware(request)

        assert mock_get_response.call_args == mock.call(request)
