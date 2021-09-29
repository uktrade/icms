from web.utils.db import show_queries
from web.utils.lock_manager import LockManager


class ICMSMiddleware:
    """Adds request.icms which is ICMSMiddlewareContext."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.icms = ICMSMiddlewareContext()

        response = self.get_response(request)

        return response


class ICMSMiddlewareContext:
    """Request-scope ICMS stuff, currently just LockManager."""

    def __init__(self):
        self.lock_manager = LockManager()


class DBQueriesMiddleware:
    """Prints all database queries made."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        show_queries(0, show_time=True, fancy_print=True)

        return response
