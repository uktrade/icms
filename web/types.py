from django.http import HttpRequest

from web.domains.user.models import User
from web.middleware.common import ICMSMiddlewareContext


class AuthenticatedHttpRequest(HttpRequest):
    user: User
    icms: ICMSMiddlewareContext
