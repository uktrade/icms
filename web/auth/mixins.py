from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from web.auth.decorators import require_registered


class RequireRegisteredMixin(PermissionRequiredMixin, View):
    """Mixin to check that user registration is complete"""
    @method_decorator(require_registered)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
