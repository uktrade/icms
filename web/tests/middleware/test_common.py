from unittest.mock import Mock, create_autospec

import pytest
from django.http import HttpRequest
from django.urls import reverse

from web.middleware.common import (
    ICMSCurrentSiteMiddleware,
    ICMSMiddleware,
    ICMSMiddlewareContext,
)
from web.utils.lock_manager import LockManager


def test_init():
    mw = ICMSMiddleware("response")

    assert mw.get_response == "response"


def test_request_icms():
    request = Mock()
    mw = ICMSMiddleware(Mock())
    mw(request)

    assert isinstance(request.icms, ICMSMiddlewareContext)
    assert isinstance(request.icms.lock_manager, LockManager)


class TestICMSCurrentSiteMiddleware:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.request = create_autospec(HttpRequest)
        self.request.get_host.return_value = "import-a-licence"

    def test_request_site_not_added(self):
        self.request.path = reverse("dbt-platform-health-check")

        middleware = ICMSCurrentSiteMiddleware(Mock())
        middleware(self.request)

        assert not hasattr(self.request, "site")

    def test_request_site_added(self):
        self.request.path = reverse("workbasket")

        middleware = ICMSCurrentSiteMiddleware(Mock())
        middleware(self.request)

        assert hasattr(self.request, "site")
