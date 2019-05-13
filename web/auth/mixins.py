from web.auth.decorators import require_registered
from django.utils.decorators import method_decorator


class RequireRegisteredMixin(object):
    """Mixin to check that user registration is complete"""

    @method_decorator(require_registered)
    def dispatch(self, *args, **kwargs):
        return super(RequireRegisteredMixin, self).dispatch(*args, **kwargs)
