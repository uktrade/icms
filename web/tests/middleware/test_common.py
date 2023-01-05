from unittest.mock import Mock

from web.middleware.common import ICMSMiddleware, ICMSMiddlewareContext
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


def test_foo():
    assert 1 == 1
