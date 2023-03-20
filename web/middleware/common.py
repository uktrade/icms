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

        # importing this at file-level causes non-local environments to fail,
        # since they don't have pygments etc installed which this module needs
        from web.utils.db import show_queries

        show_queries(ignore=0, show_time=True, fancy_print=True, msg="")

        return response
